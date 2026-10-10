from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.institute_app.models import Institute, InstituteMembership


class InstituteAdminTests(TestCase):
    def test_platform_superuser_can_create_institute_and_assign_owner(self):
        platform_admin = get_user_model().objects.create_superuser(
            username="platform-admin",
            password="test-password",
        )
        self.client.force_login(platform_admin)

        response = self.client.get(reverse("admin:institute_app_institute_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="institute_name"')
        self.assertContains(response, 'name="memberships-0-user"')

    def test_platform_superuser_can_open_institute_details(self):
        platform_admin = get_user_model().objects.create_superuser(
            username="platform-detail-admin",
            password="test-password",
        )
        owner = get_user_model().objects.create_user(
            username="detail-owner",
            password="test-password",
        )
        institute = Institute.objects.create(
            institute_code="DETAIL",
            institute_name="Institute Detail Test",
        )
        InstituteMembership.objects.create(institute=institute, user=owner)
        self.client.force_login(platform_admin)

        response = self.client.get(
            reverse(
                "admin:institute_app_institute_change",
                args=[institute.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Institute Detail Test")
        self.assertContains(response, "detail-owner")
