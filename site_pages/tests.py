from django.test import TestCase, override_settings
from django.urls import reverse


class LandingPageTests(TestCase):
    def test_landing_page_renders_base_template(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "site_pages/landing.html")
        self.assertContains(response, "Every scale,")
        self.assertContains(response, "<em>verified.</em>")
        self.assertContains(response, "LEGAL METROLOGY")
        self.assertContains(response, "Index of participants")
        self.assertContains(response, "How it works")
        self.assertContains(response, "Live ledger")
        self.assertContains(response, "Verify any certificate")
        self.assertContains(response, "footer-wordmark")
        self.assertContains(response, "motion.js")
        self.assertContains(response, "gsap.min.js")
        self.assertContains(response, "ScrollTrigger.min.js")
        self.assertContains(response, "lenis.min.js")
        self.assertContains(response, "line-mask")
        self.assertContains(response, "stat-counter")
        self.assertIn("instruments_verified", response.context)
        self.assertIn("certificates_active", response.context)
        self.assertIn("avg_days_to_certify", response.context)


class StyleguideTests(TestCase):
    @override_settings(DEBUG=True)
    def test_styleguide_available_in_debug(self):
        response = self.client.get(reverse("styleguide"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "site_pages/styleguide.html")
        self.assertContains(response, "Component & Type Specimen")
        self.assertContains(response, "Every scale, <em>verified.</em>")
        self.assertContains(response, "status-chip status-ok")
        self.assertContains(response, "stat-block")
        self.assertContains(response, "table-row")
        self.assertContains(response, "empty-state")

    @override_settings(DEBUG=False)
    def test_styleguide_hidden_when_debug_false(self):
        response = self.client.get(reverse("styleguide"))
        self.assertEqual(response.status_code, 404)
