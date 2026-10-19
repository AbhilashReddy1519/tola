from django.test import TestCase
from django.urls import reverse


class LandingPageTests(TestCase):
    def test_landing_page_renders_base_template(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "Tola")
