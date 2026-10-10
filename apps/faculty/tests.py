from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.faculty.admin import FacultyAdminForm
from apps.faculty.models import (
    Faculty,
    FacultyAddress,
    FacultyContact,
    FacultyQualification,
)
from apps.institute_app.models import (
    Campus,
    Department,
    Institute,
    InstituteMembership,
)


class FacultyCitiesApiTests(TestCase):
    @patch("apps.faculty.api_views.requests.get")
    def test_city_api_returns_cities_for_selected_country_and_state(
        self,
        mock_get,
    ):
        upstream_response = mock_get.return_value
        upstream_response.json.return_value = {
            "error": False,
            "data": [
                "Alībāg",
                "Alibag",
                "Pune",
                "Pune",
                None,
            ],
        }

        response = self.client.get(
            "/api/faculty/cities/",
            {"country": "India", "state": "Maharashtra"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], ["Alibag", "Pune"])
        mock_get.assert_called_once_with(
            "https://countriesnow.space/api/v0.1/countries/state/cities/q",
            params={"country": "India", "state": "Maharashtra"},
            timeout=10,
        )

    def test_city_api_requires_country_and_state(self):
        response = self.client.get(
            "/api/faculty/cities/",
            {"country": "India"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Country and state are required.",
        )


class FacultyPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        institute = Institute.objects.create(
            institute_code="TEST",
            institute_name="Test Institute",
        )
        cls.owner = get_user_model().objects.create_user(
            username="faculty-owner",
            password="test-password",
        )
        InstituteMembership.objects.create(institute=institute, user=cls.owner)
        cls.campus = Campus.objects.create(
            institute=institute,
            campus_code="MAIN",
            campus_name="Main Campus",
        )

        for index in range(7):
            Faculty.objects.create(
                emp_id=f"EMP{index:03d}",
                full_name=f"Faculty Member {index:02d}",
                date_of_birth=date(1980, 1, 1),
                gender="Other",
                joining_date=date(2020, 1, 1),
                employment="Permanent",
                campus=cls.campus,
            )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_faculty_list_is_paginated_on_initial_render(self):
        response = self.client.get(reverse("faculty_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["faculties"]), 5)
        self.assertEqual(response.context["paginator"].count, 7)
        self.assertContains(response, 'hx-get="/faculty/table/?page=2"')
        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, "Previous")
        self.assertContains(response, "disabled")
        self.assertRegex(
            response.content.decode(),
            r"Showing\s*<strong>\s*5\s*</strong>\s*of\s*<strong>\s*7\s*</strong>",
        )

    def test_faculty_table_pagination_keeps_filters(self):
        response = self.client.get(
            reverse("faculty_table"),
            {"page": 2, "search": "Faculty Member", "status": "active"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(response.context["paginator"].count, 7)
        self.assertContains(response, "Faculty Member 05")
        self.assertContains(response, "Page 2 of 2")
        self.assertContains(response, "hx-include=\"#facultyFilters\"")
        self.assertContains(response, "hx-get=\"/faculty/table/?page=1\"")
        self.assertRegex(
            response.content.decode(),
            r"Showing\s*<strong>\s*2\s*</strong>\s*of\s*<strong>\s*7\s*</strong>",
        )

    @override_settings(
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
    )
    def test_faculty_update_displays_existing_profile_photo(self):
        faculty = Faculty.objects.get(emp_id="EMP000")
        faculty.profile_photo = "faculty/profile/current.jpg"
        faculty.save(update_fields=["profile_photo"])

        response = self.client.get(
            reverse("faculty_update", args=[faculty.faculty_id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'src="/media/faculty/profile/current.jpg"',
        )
        self.assertContains(
            response,
            f'alt="Current profile photo of {faculty.full_name}"',
        )

    def test_faculty_pages_hide_other_institutes_records(self):
        other_institute = Institute.objects.create(
            institute_code="OTHER",
            institute_name="Other Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="OTHER-MAIN",
            campus_name="Other Campus",
        )
        other_faculty = Faculty.objects.create(
            emp_id="OTHER-EMP-001",
            full_name="Private Other Faculty",
            date_of_birth=date(1980, 1, 1),
            gender="Other",
            joining_date=date(2020, 1, 1),
            employment="Permanent",
            campus=other_campus,
        )

        list_response = self.client.get(reverse("faculty_list"))
        detail_response = self.client.get(
            reverse("faculty_detail", args=[other_faculty.faculty_id])
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, "Private Other Faculty")
        self.assertEqual(detail_response.status_code, 404)

    def test_institute_membership_scopes_faculty_even_for_superuser_account(self):
        other_institute = Institute.objects.create(
            institute_code="SUPER-OTHER",
            institute_name="Other Superuser Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="SUPER-OTHER-MAIN",
            campus_name="Other Superuser Campus",
        )
        Faculty.objects.create(
            emp_id="SUPER-OTHER-EMP",
            full_name="Private Superuser Institute Faculty",
            date_of_birth=date(1980, 1, 1),
            gender="Other",
            joining_date=date(2020, 1, 1),
            employment="Permanent",
            campus=other_campus,
        )
        self.owner.is_superuser = True
        self.owner.save(update_fields=["is_superuser"])

        response = self.client.get(reverse("faculty_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Faculty Member 00")
        self.assertNotContains(response, "Private Superuser Institute Faculty")

    def test_inactive_institute_membership_does_not_grant_superuser_global_access(self):
        self.owner.is_superuser = True
        self.owner.save(update_fields=["is_superuser"])
        Institute.objects.filter(campuses=self.campus).update(status=False)

        response = self.client.get(reverse("faculty_list"))

        self.assertEqual(response.status_code, 403)


class FacultyCreateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        institute = Institute.objects.create(
            institute_code="CREATE",
            institute_name="Create Test Institute",
        )
        cls.owner = get_user_model().objects.create_user(
            username="faculty-create-owner",
            password="test-password",
        )
        InstituteMembership.objects.create(institute=institute, user=cls.owner)
        cls.campus = Campus.objects.create(
            institute=institute,
            campus_code="CREATE-MAIN",
            campus_name="Create Test Campus",
        )
        cls.department = Department.objects.create(
            campus=cls.campus,
            department_code="CREATE-CSE",
            department_name="Computer Science",
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def faculty_payload(self, emp_id="EMP-CREATE-001"):
        return {
            "emp_id": emp_id,
            "full_name": "Test Faculty",
            "campus": str(self.campus.campus_id),
            "date_of_birth": "1985-01-15",
            "gender": "Other",
            "joining_date": "2024-01-15",
            "employment": "Full Time",
            "status": "1",
            "email": "faculty@example.com",
            "phone_number": "1234567890",
            "address": "1 Test Street",
            "city": "Test City",
            "state": "Test State",
            "country": "India",
            "pincode": "123456",
            "department": str(self.department.department_id),
            "designation": "Assistant Professor",
            "qualification": "M.Tech",
            "specialization": "Computer Science",
            "experience": "5",
        }

    def test_valid_submission_creates_faculty_and_related_records(self):
        response = self.client.post(
            reverse("faculty_add"),
            self.faculty_payload(),
        )

        self.assertEqual(response.status_code, 302)
        faculty = Faculty.objects.get(emp_id="EMP-CREATE-001")
        self.assertTrue(FacultyContact.objects.filter(faculty=faculty).exists())
        self.assertTrue(FacultyAddress.objects.filter(faculty=faculty).exists())
        self.assertTrue(
            FacultyQualification.objects.filter(faculty=faculty).exists()
        )

    def test_save_error_is_visible_and_transaction_leaves_no_partial_record(self):
        Faculty.objects.create(
            emp_id="EMP-CREATE-001",
            full_name="Existing Faculty",
            date_of_birth="1980-01-01",
            gender="Other",
            joining_date="2020-01-01",
            employment="Full Time",
            campus=self.campus,
        )

        response = self.client.post(
            reverse("faculty_add"),
            self.faculty_payload(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unable to Create Faculty:")
        self.assertEqual(
            Faculty.objects.filter(emp_id="EMP-CREATE-001").count(),
            1,
        )

    def test_cannot_create_faculty_in_another_institutes_campus(self):
        other_institute = Institute.objects.create(
            institute_code="OTHER",
            institute_name="Other Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="OTHER-MAIN",
            campus_name="Other Campus",
        )
        other_department = Department.objects.create(
            campus=other_campus,
            department_code="OTHER-CSE",
            department_name="Other Computer Science",
        )
        payload = self.faculty_payload("EMP-FOREIGN-001")
        payload.update({
            "campus": str(other_campus.campus_id),
            "department": str(other_department.department_id),
        })

        response = self.client.post(reverse("faculty_add"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a campus belonging to your institute.")
        self.assertFalse(Faculty.objects.filter(emp_id="EMP-FOREIGN-001").exists())

    def test_employee_id_can_be_reused_in_a_different_institute(self):
        other_institute = Institute.objects.create(
            institute_code="EMP-OTHER",
            institute_name="Other Employee Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="EMP-OTHER-MAIN",
            campus_name="Other Employee Campus",
        )
        other_department = Department.objects.create(
            campus=other_campus,
            department_code="EMP-OTHER-CSE",
            department_name="Other Computer Science",
        )
        Faculty.objects.create(
            emp_id="SHARED-EMP-001",
            full_name="Faculty At Other Institute",
            date_of_birth=date(1980, 1, 1),
            gender="Other",
            joining_date=date(2020, 1, 1),
            employment="Permanent",
            campus=other_campus,
        )
        payload = self.faculty_payload("SHARED-EMP-001")

        response = self.client.post(reverse("faculty_add"), payload)

        self.assertEqual(response.status_code, 302)
        faculty = Faculty.objects.get(
            emp_id="SHARED-EMP-001",
            campus=self.campus,
        )
        self.assertEqual(faculty.institute_id, self.campus.institute_id)

    def test_duplicate_employee_id_is_still_rejected_inside_same_institute(self):
        Faculty.objects.create(
            emp_id="SAME-INSTITUTE-001",
            full_name="Existing Institute Faculty",
            date_of_birth=date(1980, 1, 1),
            gender="Other",
            joining_date=date(2020, 1, 1),
            employment="Permanent",
            campus=self.campus,
        )

        response = self.client.post(
            reverse("faculty_add"),
            self.faculty_payload("SAME-INSTITUTE-001"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This employee ID is already used in this institute.",
        )
        self.assertEqual(
            Faculty.objects.filter(
                institute=self.campus.institute,
                emp_id="SAME-INSTITUTE-001",
            ).count(),
            1,
        )

    def test_admin_form_allows_employee_id_used_in_another_institute(self):
        other_institute = Institute.objects.create(
            institute_code="ADMIN-OTHER",
            institute_name="Other Admin Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="ADMIN-OTHER-MAIN",
            campus_name="Other Admin Campus",
        )
        Faculty.objects.create(
            emp_id="ADMIN-SHARED-001",
            full_name="Faculty In Other Institute",
            date_of_birth=date(1980, 1, 1),
            gender="Other",
            joining_date=date(2020, 1, 1),
            employment="Permanent",
            campus=other_campus,
        )

        form = FacultyAdminForm(data={
            "emp_id": "ADMIN-SHARED-001",
            "full_name": "Faculty In This Institute",
            "date_of_birth": "1980-01-01",
            "gender": "Other",
            "joining_date": "2020-01-01",
            "employment": "Permanent",
            "status": "on",
            "campus": str(self.campus.pk),
        })

        self.assertTrue(form.is_valid(), form.errors)


class FacultyUserLinkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        institute = Institute.objects.create(
            institute_code="USER-LINK",
            institute_name="User Link Institute",
        )
        campus = Campus.objects.create(
            institute=institute,
            campus_code="USER-LINK-MAIN",
            campus_name="User Link Campus",
        )
        cls.faculty = Faculty.objects.create(
            emp_id="USER-LINK-001",
            full_name="Linked Faculty",
            date_of_birth=date(1980, 1, 1),
            gender="Other",
            joining_date=date(2020, 1, 1),
            employment="Permanent",
            campus=campus,
        )
        cls.faculty_user = get_user_model().objects.create_user(
            username="linked-faculty",
            email="linked-faculty@example.com",
            password="A-strong-test-password-123",
        )
        cls.owner_user = get_user_model().objects.create_user(
            username="linked-institute-owner",
            email="linked-owner@example.com",
            password="A-strong-test-password-123",
        )
        InstituteMembership.objects.create(
            institute=institute,
            user=cls.owner_user,
        )

    def test_faculty_can_be_linked_to_one_login_user(self):
        self.faculty.user = self.faculty_user
        self.faculty.save(update_fields=["user"])

        self.assertEqual(self.faculty.user, self.faculty_user)
        self.assertEqual(self.faculty_user.faculty_profile, self.faculty)

    def test_deleting_login_user_keeps_faculty_profile(self):
        self.faculty.user = self.faculty_user
        self.faculty.save(update_fields=["user"])

        self.faculty_user.delete()

        self.faculty.refresh_from_db()
        self.assertIsNone(self.faculty.user)

    def test_admin_form_only_offers_unassigned_non_superuser_accounts(self):
        superuser = get_user_model().objects.create_superuser(
            username="platform-superuser",
            email="platform@example.com",
            password="A-strong-test-password-123",
        )
        form = FacultyAdminForm()
        available_users = form.fields["user"].queryset

        self.assertIn(self.faculty_user, available_users)
        self.assertNotIn(self.owner_user, available_users)
        self.assertNotIn(superuser, available_users)

        linked_faculty = Faculty.objects.get(pk=self.faculty.pk)
        linked_faculty.user = self.faculty_user
        linked_faculty.save(update_fields=["user"])
        self.assertNotIn(
            self.faculty_user,
            FacultyAdminForm().fields["user"].queryset,
        )
