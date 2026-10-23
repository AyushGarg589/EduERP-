from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.institute_app.models import Institute, InstituteMembership


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="admin",
            email="admin@example.com",
            password="A-secure-test-password",
        )

    def test_admin_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:admin_dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('public:login_page')}?next={reverse('dashboard:admin_dashboard')}",
        )

    def test_admin_dashboard_uses_shared_dashboard_base(self):
        self.client.force_login(self.user)
        institute = Institute.objects.create(
            institute_code="DASH",
            institute_name="Dashboard Institute",
        )
        InstituteMembership.objects.create(institute=institute, user=self.user)

        response = self.client.get(reverse("dashboard:admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/admin_dashboard.html")
        self.assertTemplateUsed(response, "dashboard/dashboard_base.html")
        self.assertContains(response, "Welcome back, admin")
        self.assertContains(
            response,
            f'<a href="{reverse("students:student_list")}"><i class="fa-solid fa-user"></i><span>Student List</span></a>',
        )
        self.assertContains(
            response,
            f'<a href="{reverse("faculty_list")}"><i class="fa-solid fa-user-tie"></i><span>Faculties</span></a>',
        )

    def test_login_redirects_to_admin_dashboard(self):
        institute = Institute.objects.create(
            institute_code="LOGIN",
            institute_name="Login Institute",
        )
        InstituteMembership.objects.create(institute=institute, user=self.user)

        response = self.client.post(
            reverse("public:login_page"),
            {"user-email": "admin@example.com", "user-password": "A-secure-test-password"},
        )

        self.assertRedirects(response, reverse("dashboard:admin_dashboard"))

    def test_ajax_login_returns_admin_dashboard_url(self):
        response = self.client.post(
            reverse("public:login_page"),
            {"user-email": "admin@example.com", "user-password": "A-secure-test-password"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_url"], reverse("dashboard:admin_dashboard"))

    def test_logout_ends_session_and_redirects_home(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("dashboard:logout_home"))

        self.assertRedirects(response, reverse("public:home"))
        self.assertNotIn("_auth_user_id", self.client.session)
