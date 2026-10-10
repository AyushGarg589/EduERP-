import base64
import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.institute_app.models import (
    Campus,
    Course,
    Department,
    Institute,
    InstituteMembership,
)
from apps.students.models import Student, StudentContact, StudentEnrollment


class StudentListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        institute = Institute.objects.create(
            institute_code="TEST",
            institute_name="Test Institute",
        )
        cls.owner = get_user_model().objects.create_user(
            username="student-owner",
            password="test-password",
        )
        InstituteMembership.objects.create(institute=institute, user=cls.owner)
        campus = Campus.objects.create(
            institute=institute,
            campus_code="MAIN",
            campus_name="Main Campus",
        )
        cse = Department.objects.create(
            campus=campus,
            department_code="CSE",
            department_name="Computer Science",
        )
        ece = Department.objects.create(
            campus=campus,
            department_code="ECE",
            department_name="Electronics",
        )
        btech = Course.objects.create(
            department=cse,
            campus=campus,
            course_code="BTECH-CSE",
            course_name="B.Tech",
            course_type="UG",
            duration="4 Years",
            semesters=8,
        )
        bca = Course.objects.create(
            department=ece,
            campus=campus,
            course_code="BCA",
            course_name="BCA",
            course_type="UG",
            duration="3 Years",
            semesters=6,
        )

        cls.active_student = Student.objects.create(
            campus=campus,
            full_name="Asha Mehta",
            date_of_birth=date(2005, 5, 10),
            gender="Female",
            status=True,
        )
        StudentContact.objects.create(
            student=cls.active_student,
            email="asha@example.com",
            phone_number="1234567890",
        )
        StudentEnrollment.objects.create(
            student=cls.active_student,
            course=btech,
            branch=cse,
            campus=campus,
            academic_year="2026-27",
            semester=3,
            section="A",
            roll_no="A001",
        )

        cls.inactive_student = Student.objects.create(
            campus=campus,
            full_name="Ravi Shah",
            date_of_birth=date(2004, 7, 12),
            gender="Male",
            status=False,
        )
        StudentContact.objects.create(
            student=cls.inactive_student,
            email="ravi@example.com",
            phone_number="0987654321",
        )
        StudentEnrollment.objects.create(
            student=cls.inactive_student,
            course=bca,
            branch=ece,
            campus=campus,
            academic_year="2026-27",
            semester=2,
            section="B",
            roll_no="R002",
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_student_list_renders_database_records_and_filter_options(self):
        response = self.client.get(reverse("student_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha Mehta")
        self.assertContains(response, "Ravi Shah")
        self.assertContains(response, "Electronics")
        self.assertContains(response, 'hx-trigger="load"')

    def test_student_edit_and_detail_display_profile_photo(self):
        self.active_student.profile_photo = "students/profile/asha.jpg"
        self.active_student.save(update_fields=["profile_photo"])

        edit_response = self.client.get(
            reverse("student_update", args=[self.active_student.student_id])
        )
        detail_response = self.client.get(
            reverse("student_detail", args=[self.active_student.student_id])
        )

        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(edit_response, 'enctype="multipart/form-data"')
        self.assertContains(edit_response, 'type="file"')
        self.assertContains(edit_response, 'name="profile_photo"')
        self.assertContains(edit_response, 'name="profile_photo-clear"')
        self.assertContains(edit_response, 'for="id_profile_photo-clear"')
        self.assertContains(edit_response, 'check “Clear” to remove it')
        self.assertContains(edit_response, "/media/students/profile/asha.jpg")

        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "/media/students/profile/asha.jpg")
        self.assertContains(detail_response, 'alt="Asha Mehta"')

    def test_student_edit_saves_uploaded_profile_photo(self):
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lS8AAAAASUVORK5CYII="
        )
        photo = SimpleUploadedFile(
            "new-profile.png",
            png_data,
            content_type="image/png",
        )

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("student_update", args=[self.active_student.student_id]),
                    {
                        "full_name": self.active_student.full_name,
                        "date_of_birth": "2005-05-10",
                        "gender": self.active_student.gender,
                        "blood_group": "",
                        "campus": self.active_student.campus_id,
                        "status": "on",
                        "profile_photo": photo,
                    },
                )

                self.assertRedirects(
                    response,
                    reverse("student_detail", args=[self.active_student.student_id]),
                )
                self.active_student.refresh_from_db()
                self.assertTrue(self.active_student.profile_photo.name)
                self.assertTrue(Path(self.active_student.profile_photo.path).is_file())

    def test_htmx_table_filters_by_search_course_department_and_status(self):
        response = self.client.get(
            reverse("student_table"),
            {
                "search": "asha@example.com",
                "course": "B.Tech",
                "branch": "Computer Science",
                "status": "active",
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha Mehta")
        self.assertNotContains(response, "Ravi Shah")
        self.assertContains(response, "Showing <strong>1</strong> of <strong>1</strong>")

    def test_htmx_table_renders_student_avatar_photo_and_fallback(self):
        self.active_student.profile_photo = "students/profile/asha.jpg"
        self.active_student.save(update_fields=["profile_photo"])

        response = self.client.get(
            reverse("student_table"),
            {"search": "Asha Mehta"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'src="/media/students/profile/asha.jpg"',
        )
        self.assertContains(
            response,
            'onerror="this.hidden = true; this.nextElementSibling.hidden = false;"',
        )
        self.assertContains(response, "<span hidden>")
        self.assertContains(response, "A")

    def test_htmx_table_paginates_filtered_students(self):
        for index in range(10):
            Student.objects.create(
                campus=self.active_student.campus,
                full_name=f"Extra Student {index:02d}",
                date_of_birth=date(2005, 1, 1),
                gender="Female",
                status=True,
            )

        first_page = self.client.get(
            reverse("student_table"),
            {"status": "active"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(first_page.context["page_obj"].number, 1)
        self.assertEqual(first_page.context["page_obj"].paginator.count, 11)
        self.assertTrue(first_page.context["page_obj"].has_next())
        self.assertContains(first_page, "hx-include=\"#studentFilters\"")

        second_page = self.client.get(
            reverse("student_table"),
            {"status": "active", "page": 2},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(second_page.context["page_obj"].number, 2)
        self.assertEqual(second_page.context["page_obj"].paginator.count, 11)
        self.assertContains(second_page, "Extra Student 09")
        self.assertNotContains(second_page, "Ravi Shah")
        self.assertContains(second_page, "Showing <strong>1</strong> of <strong>11</strong>")

    def test_htmx_table_search_accepts_formatted_student_id(self):
        response = self.client.get(
            reverse("student_table"),
            {"search": f"STU{self.active_student.student_id:03d}"},
            HTTP_HX_REQUEST="true",
        )

        self.assertContains(response, "Asha Mehta")
        self.assertNotContains(response, "Ravi Shah")

    def test_htmx_table_shows_empty_state_for_no_matches(self):
        response = self.client.get(
            reverse("student_table"),
            {"search": "nobody@example.com"},
            HTTP_HX_REQUEST="true",
        )

        self.assertContains(response, "No students match these filters")
        self.assertNotContains(response, "Asha Mehta")
        self.assertNotContains(response, "Ravi Shah")

    def test_student_pages_and_apis_hide_other_institutes_records(self):
        other_institute = Institute.objects.create(
            institute_code="OTHER",
            institute_name="Other Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="OTHER-MAIN",
            campus_name="Other Campus",
        )
        other_student = Student.objects.create(
            campus=other_campus,
            full_name="Private Other Student",
            date_of_birth=date(2005, 1, 1),
            gender="Other",
        )

        page_response = self.client.get(reverse("student_list"))
        table_response = self.client.get(reverse("student_table"))
        list_api_response = self.client.get(reverse("student_api_list"))
        detail_api_response = self.client.get(
            reverse("studentDetail", args=[other_student.student_id])
        )

        self.assertEqual(page_response.status_code, 200)
        self.assertNotContains(page_response, "Private Other Student")
        self.assertEqual(table_response.status_code, 200)
        self.assertNotContains(table_response, "Private Other Student")
        self.assertEqual(list_api_response.status_code, 200)
        self.assertNotIn(
            "Private Other Student",
            [student["full_name"] for student in list_api_response.json()["data"]],
        )
        self.assertEqual(detail_api_response.status_code, 404)

    def test_student_create_rejects_another_institutes_campus(self):
        other_institute = Institute.objects.create(
            institute_code="OTHER-CREATE",
            institute_name="Other Create Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="OTHER-CREATE-MAIN",
            campus_name="Other Create Campus",
        )

        response = self.client.post(
            reverse("student_add"),
            {"campus": str(other_campus.campus_id)},
        )

        self.assertRedirects(response, reverse("student_add"))
        self.assertFalse(
            Student.objects.filter(campus=other_campus).exists()
        )

    def test_student_api_rejects_another_institutes_campus(self):
        other_institute = Institute.objects.create(
            institute_code="OTHER-API",
            institute_name="Other API Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="OTHER-API-MAIN",
            campus_name="Other API Campus",
        )
        response = self.client.post(
            reverse("createStudent"),
            json.dumps({
                "campus": other_campus.campus_id,
                "full_name": "Foreign API Student",
                "date_of_birth": "2005-01-01",
                "gender": "Other",
                "status": True,
                "contact": {
                    "email": "foreign@example.com",
                    "phone_number": "1234567890",
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Student.objects.filter(full_name="Foreign API Student").exists()
        )

    def test_student_access_requires_an_institute_membership(self):
        unassigned_user = get_user_model().objects.create_user(
            username="unassigned-student-user",
            password="test-password",
        )
        self.client.force_login(unassigned_user)

        page_response = self.client.get(reverse("student_list"))
        api_response = self.client.get(reverse("student_api_list"))

        self.assertEqual(page_response.status_code, 403)
        self.assertEqual(api_response.status_code, 403)

    def test_uploaded_files_are_only_served_to_their_institute(self):
        other_institute = Institute.objects.create(
            institute_code="MEDIA",
            institute_name="Media Institute",
        )
        other_campus = Campus.objects.create(
            institute=other_institute,
            campus_code="MEDIA-MAIN",
            campus_name="Media Campus",
        )
        other_student = Student.objects.create(
            campus=other_campus,
            full_name="Media Student",
            date_of_birth=date(2005, 1, 1),
            gender="Other",
            profile_photo="students/profile/private.jpg",
        )
        other_owner = get_user_model().objects.create_user(
            username="media-owner",
            password="test-password",
        )
        InstituteMembership.objects.create(
            institute=other_institute,
            user=other_owner,
        )

        with TemporaryDirectory() as media_root:
            private_file = Path(media_root) / "students" / "profile" / "private.jpg"
            private_file.parent.mkdir(parents=True)
            private_file.write_bytes(b"private institute file")

            with override_settings(MEDIA_ROOT=media_root):
                media_url = "/media/students/profile/private.jpg"
                owner_response = self.client.get(media_url)
                self.client.force_login(other_owner)
                other_owner_response = self.client.get(media_url)
                other_owner_file_content = b"".join(
                    other_owner_response.streaming_content
                )
                other_owner_response.close()

        self.assertEqual(owner_response.status_code, 404)
        self.assertEqual(other_owner_response.status_code, 200)
        self.assertEqual(other_owner_file_content, b"private institute file")
