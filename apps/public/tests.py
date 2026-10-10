from django.contrib.admin.sites import site
from django.test import TestCase

from .models import RegisterUser


class RegisterUserAdminTests(TestCase):
    def test_registeruser_model_is_registered_in_admin(self):
        self.assertIn(RegisterUser, site._registry)

    def test_registeruser_admin_has_expected_display_fields(self):
        model_admin = site._registry[RegisterUser]
        self.assertIn("name", model_admin.list_display)
        self.assertIn("email", model_admin.list_display)
        self.assertIn("phone_number", model_admin.list_display)
