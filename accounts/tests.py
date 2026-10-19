from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

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
            username="admin_user",
            password="adminpassword",
            role=User.Role.ADMIN,
        )
        self.assertEqual(admin_user.role, User.Role.ADMIN)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class AuthAndRoleTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_user",
            password="password123",
            role=User.Role.OWNER,
        )
        self.inspector = User.objects.create_user(
            username="inspector_user",
            password="password123",
            role=User.Role.INSPECTOR,
        )
        self.admin = User.objects.create_user(
            username="admin_user",
            password="password123",
            role=User.Role.ADMIN,
        )

    def test_anonymous_user_redirected_to_login(self):
        endpoints = [
            reverse("app_redirect"),
            reverse("owner_dashboard"),
            reverse("inspector_queue"),
            reverse("admin_console"),
        ]
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response.url)

    def test_owner_cannot_open_inspector_url(self):
        self.client.login(username="owner_user", password="password123")
        response = self.client.get(reverse("inspector_queue"))
        self.assertEqual(response.status_code, 403)

    def test_owner_cannot_open_admin_console(self):
        self.client.login(username="owner_user", password="password123")
        response = self.client.get(reverse("admin_console"))
        self.assertEqual(response.status_code, 403)

    def test_inspector_cannot_open_owner_dashboard(self):
        self.client.login(username="inspector_user", password="password123")
        response = self.client.get(reverse("owner_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_app_redirect_for_each_role(self):
        # Owner
        self.client.login(username="owner_user", password="password123")
        response = self.client.get(reverse("app_redirect"))
        self.assertRedirects(response, reverse("instrument_list"))
        self.client.logout()

        # Inspector
        self.client.login(username="inspector_user", password="password123")
        response = self.client.get(reverse("app_redirect"))
        self.assertRedirects(response, reverse("inspector_queue"))
        self.client.logout()

        # Admin
        self.client.login(username="admin_user", password="password123")
        response = self.client.get(reverse("app_redirect"))
        self.assertRedirects(response, reverse("admin_console"))
        self.client.logout()

    def test_stub_pages_content(self):
        self.client.login(username="owner_user", password="password123")
        response = self.client.get(reverse("owner_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner dashboard")
        self.client.logout()

        self.client.login(username="inspector_user", password="password123")
        response = self.client.get(reverse("inspector_queue"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inspector queue")
        self.client.logout()

        self.client.login(username="admin_user", password="password123")
        response = self.client.get(reverse("admin_console"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin console")
        self.client.logout()

    def test_logout_view_get_and_post(self):
        # Test GET logout
        self.client.login(username="owner_user", password="password123")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("landing"))
        self.assertNotIn("_auth_user_id", self.client.session)

        # Test POST logout
        self.client.login(username="owner_user", password="password123")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("landing"))
        self.assertNotIn("_auth_user_id", self.client.session)


class OwnerRegistrationTests(TestCase):
    def test_owner_registration_success(self):
        data = {
            "username": "new_owner",
            "email": "new_owner@example.com",
            "phone": "9876543219",
            "password1": "SecretPassword123!",
            "password2": "SecretPassword123!",
        }
        response = self.client.post(reverse("register"), data)
        self.assertRedirects(response, reverse("app_redirect"), target_status_code=302)
        user = User.objects.get(username="new_owner")
        self.assertEqual(user.role, User.Role.OWNER)
        self.assertEqual(user.phone, "9876543219")
        self.assertEqual(user.email, "new_owner@example.com")

    def test_registration_cannot_set_role_to_admin(self):
        data = {
            "username": "sneaky_user",
            "email": "sneaky@example.com",
            "phone": "9876543218",
            "password1": "SecretPassword123!",
            "password2": "SecretPassword123!",
            "role": "ADMIN",  # Attempt to elevate role
            "is_staff": "True",
            "is_superuser": "True",
        }
        response = self.client.post(reverse("register"), data)
        self.assertRedirects(response, reverse("app_redirect"), target_status_code=302)
        user = User.objects.get(username="sneaky_user")
        self.assertEqual(user.role, User.Role.OWNER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_register_page_renders_styled_components(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create <em>account</em>")
        self.assertContains(response, "class=\"field\"")
        self.assertContains(response, "class=\"btn btn-primary\"")

    def test_login_page_renders_styled_components(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign <em>in</em>")
        self.assertContains(response, "class=\"field\"")
        self.assertContains(response, "class=\"btn btn-primary\"")
        self.assertContains(response, "DEMO CREDENTIALS")
        self.assertContains(response, "owner_ramesh")


class ManagementCommandTests(TestCase):
    def test_create_demo_users_command(self):
        call_command("create_demo_users")
        self.assertTrue(User.objects.filter(username="admin", role=User.Role.ADMIN).exists())
        self.assertTrue(User.objects.filter(username="inspector_rajesh", role=User.Role.INSPECTOR).exists())
        self.assertTrue(User.objects.filter(username="owner_ramesh", role=User.Role.OWNER).exists())
        self.assertTrue(User.objects.filter(username="owner_priya", role=User.Role.OWNER).exists())
