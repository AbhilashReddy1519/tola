import datetime
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registry.models import AccuracyClass, Business, Category, Instrument, TradeType, Unit
from verification.models import Inspection, InspectionResult, RequestStatus, VerificationRequest
from .models import Certificate
from .services import generate_certificate_number, issue_certificate, revoke_certificate

User = get_user_model()


class CertificateIssuanceAndModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="cert_owner", password="password123", role=User.Role.OWNER,
            email="secret.owner@example.com", phone="9999999999"
        )
        self.biz = Business.objects.create(
            owner=self.owner, name="Cert Test Grocers", trade_type=TradeType.GROCERY,
            address="Plot 10", district="Hyderabad", pincode="500001"
        )
        self.instrument = Instrument.objects.create(
            business=self.biz, category=Category.COUNTER_SCALE,
            make="Avery", model_no="AT-10", serial_no="CERT-INST-01",
            max_capacity=Decimal("15"), unit=Unit.KG,
            scale_interval_e=Decimal("0.005"), accuracy_class=AccuracyClass.CLASS_III
        )
        self.inspector = User.objects.create_user(
            username="cert_inspector", password="password123", role=User.Role.INSPECTOR
        )
        self.req_pass = VerificationRequest.objects.create(
            instrument=self.instrument, requested_by=self.owner,
            preferred_date="2026-11-01", status=RequestStatus.PASSED,
            inspector=self.inspector
        )
        self.inspection_pass = Inspection.objects.create(
            request=self.req_pass, inspector=self.inspector,
            zero_ok=True, result=InspectionResult.PASS, remarks="Good calibration"
        )

        self.req_fail = VerificationRequest.objects.create(
            instrument=self.instrument, requested_by=self.owner,
            preferred_date="2026-11-01", status=RequestStatus.FAILED,
            inspector=self.inspector
        )
        self.inspection_fail = Inspection.objects.create(
            request=self.req_fail, inspector=self.inspector,
            zero_ok=True, result=InspectionResult.FAIL, remarks="MPE Exceeded"
        )

    def test_certificate_issued_on_pass_only(self):
        # Passing inspection successfully generates certificate and marks request CERTIFIED
        cert = issue_certificate(self.inspection_pass, actor=self.inspector)
        self.assertIsNotNone(cert.pk)
        self.assertEqual(cert.state, "VALID")
        self.req_pass.refresh_from_db()
        self.assertEqual(self.req_pass.status, RequestStatus.CERTIFIED)

        # Failed inspection raises ValueError; certificate is never issued
        with self.assertRaises(ValueError):
            issue_certificate(self.inspection_fail, actor=self.inspector)
        self.assertFalse(hasattr(self.inspection_fail, "certificate"))

    def test_unique_sequential_numbers(self):
        num1 = generate_certificate_number(year=2026)
        c1 = Certificate.objects.create(
            inspection=self.inspection_pass, number=num1,
            issued_on=timezone.now().date(),
            valid_until=timezone.now().date() + datetime.timedelta(days=365)
        )
        self.assertEqual(num1, "TOLA-2026-000001")

        # Second number increments sequence
        num2 = generate_certificate_number(year=2026)
        self.assertEqual(num2, "TOLA-2026-000002")

    def test_expired_and_revoked_states(self):
        today = timezone.now().date()
        cert = Certificate.objects.create(
            inspection=self.inspection_pass,
            number="TOLA-2026-000999",
            issued_on=today - datetime.timedelta(days=400),
            valid_until=today - datetime.timedelta(days=35),  # in past
        )
        self.assertEqual(cert.state, "EXPIRED")

        # Set valid until future date -> VALID
        cert.valid_until = today + datetime.timedelta(days=100)
        cert.save()
        self.assertEqual(cert.state, "VALID")

        # Revoke certificate -> REVOKED
        revoke_certificate(cert, reason="Broken calibration seal observed during random audit")
        self.assertEqual(cert.state, "REVOKED")
        self.assertEqual(cert.revoked_reason, "Broken calibration seal observed during random audit")

    def test_instrument_derived_status_wired_to_certificate(self):
        # Fresh instrument with no certificate and no requests -> Unverified
        fresh_instrument = Instrument.objects.create(
            business=self.biz, category=Category.COUNTER_SCALE,
            make="Essae", model_no="E1", serial_no="FRESH-001",
            max_capacity=Decimal("10"), unit=Unit.KG,
            scale_interval_e=Decimal("0.005"), accuracy_class=AccuracyClass.CLASS_III
        )
        self.assertEqual(fresh_instrument.status, "Unverified")

        # Issue certificate -> Valid
        cert = issue_certificate(self.inspection_pass, actor=self.inspector)
        self.assertEqual(self.instrument.status, "Valid")
        self.assertEqual(self.instrument.current_certificate, cert)

        # Expiring soon (within 30 days)
        today = timezone.now().date()
        cert.valid_until = today + datetime.timedelta(days=15)
        cert.save()
        self.assertEqual(self.instrument.status, "Expiring soon")

        # Expired (in the past)
        cert.valid_until = today - datetime.timedelta(days=5)
        cert.save()
        self.assertEqual(self.instrument.status, "Expired")

        # If certificate revoked -> Revoked
        revoke_certificate(cert, reason="Test grounds")
        self.assertEqual(self.instrument.status, "Revoked")


class PublicVerificationViewsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="public_owner", password="password123", role=User.Role.OWNER,
            email="private.email@shop.com", phone="9876500000"
        )
        self.biz = Business.objects.create(
            owner=self.owner, name="Mandi Grain Merchants", trade_type=TradeType.GROCERY,
            address="Shop 4 Market Yard", district="Warangal", pincode="506001"
        )
        self.instrument = Instrument.objects.create(
            business=self.biz, category=Category.PLATFORM_SCALE,
            make="Essae", model_no="PR-500", serial_no="ESS-900",
            max_capacity=Decimal("500"), unit=Unit.KG,
            scale_interval_e=Decimal("0.05"), accuracy_class=AccuracyClass.CLASS_III
        )
        self.inspector = User.objects.create_user(
            username="pub_inspector", password="password123", role=User.Role.INSPECTOR
        )
        self.req = VerificationRequest.objects.create(
            instrument=self.instrument, requested_by=self.owner,
            preferred_date="2026-11-01", status=RequestStatus.PASSED,
            inspector=self.inspector
        )
        self.inspection = Inspection.objects.create(
            request=self.req, inspector=self.inspector,
            zero_ok=True, result=InspectionResult.PASS
        )
        self.cert = issue_certificate(self.inspection, actor=self.inspector)

    def test_token_lookup_success_and_privacy_guarantee(self):
        url = reverse("public_token_verify", kwargs={"token": self.cert.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Displays state word VALID at display size
        self.assertContains(response, "VALID")
        # Shows business name and instrument serial
        self.assertContains(response, "Mandi Grain Merchants")
        self.assertContains(response, "ESS-900")
        self.assertContains(response, self.cert.number)

        # STRICT PRIVACY: NEVER LEAK OWNER EMAIL OR PHONE
        self.assertNotContains(response, "private.email@shop.com")
        self.assertNotContains(response, "9876500000")

    def test_revoked_state_displayed_on_public_page(self):
        revoke_certificate(self.cert, reason="Tampered seal found by flying squad")
        url = reverse("public_token_verify", kwargs={"token": self.cert.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "REVOKED")
        self.assertContains(response, "Tampered seal found by flying squad")

    def test_invalid_token_returns_404(self):
        fake_token = uuid.uuid4()
        url = reverse("public_token_verify", kwargs={"token": fake_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_manual_verify_lookup(self):
        # Found
        url = reverse("public_manual_verify")
        response = self.client.get(url, {"number": self.cert.number})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cert.number)
        self.assertContains(response, reverse("public_token_verify", kwargs={"token": self.cert.token}))

        # Not found
        response_bad = self.client.get(url, {"number": "TOLA-9999-999999"})
        self.assertEqual(response_bad.status_code, 200)
        self.assertContains(response_bad, 'No verified certificate found')


class PDFDownloadPermissionsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="legit_owner", password="password123", role=User.Role.OWNER
        )
        self.stranger_owner = User.objects.create_user(
            username="stranger_owner", password="password123", role=User.Role.OWNER
        )
        self.admin = User.objects.create_user(
            username="admin_pdf", password="password123", role=User.Role.ADMIN
        )
        self.inspector = User.objects.create_user(
            username="insp_pdf", password="password123", role=User.Role.INSPECTOR
        )

        self.biz = Business.objects.create(
            owner=self.owner, name="Legit Scales", trade_type=TradeType.GROCERY,
            address="Addr", district="Dist", pincode="500001"
        )
        self.instrument = Instrument.objects.create(
            business=self.biz, category=Category.COUNTER_SCALE,
            make="Avery", model_no="AT", serial_no="PDF-01",
            max_capacity=Decimal("20"), unit=Unit.KG,
            scale_interval_e=Decimal("0.005"), accuracy_class=AccuracyClass.CLASS_III
        )
        self.req = VerificationRequest.objects.create(
            instrument=self.instrument, requested_by=self.owner,
            preferred_date="2026-11-01", status=RequestStatus.PASSED,
            inspector=self.inspector
        )
        self.inspection = Inspection.objects.create(
            request=self.req, inspector=self.inspector,
            zero_ok=True, result=InspectionResult.PASS
        )
        self.cert = issue_certificate(self.inspection, actor=self.inspector)
        self.pdf_url = reverse("certificate_pdf", kwargs={"number": self.cert.number})

    def test_owner_can_download_pdf(self):
        self.client.login(username="legit_owner", password="password123")
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        # Verify real PDF bytes with standard header
        self.assertTrue(response.content.startswith(b"%PDF-"))

    def test_admin_can_download_pdf(self):
        self.client.login(username="admin_pdf", password="password123")
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_stranger_owner_gets_404(self):
        self.client.login(username="stranger_owner", password="password123")
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_gets_404(self):
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 404)

    def test_inspector_gets_404(self):
        self.client.login(username="insp_pdf", password="password123")
        response = self.client.get(self.pdf_url)
        self.assertEqual(response.status_code, 404)
