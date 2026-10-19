from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_default_role(self):
        user = User.objects.create_user(
            username="testowner",
            password="password123",
            phone="9876543210",
        )
        self.assertEqual(user.role, User.Role.OWNER)
        self.assertEqual(user.phone, "9876543210")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username="admin",
            password="adminpassword",
            role=User.Role.ADMIN,
        )
        self.assertEqual(admin_user.role, User.Role.ADMIN)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
