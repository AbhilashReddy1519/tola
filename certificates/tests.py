import datetime
from io import StringIO
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
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


class AdminRevokeCertificateViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_revoker", password="password123", role=User.Role.ADMIN
        )
        self.owner = User.objects.create_user(
            username="owner_revoker", password="password123", role=User.Role.OWNER
        )
        self.inspector = User.objects.create_user(
            username="insp_revoker", password="password123", role=User.Role.INSPECTOR
        )
        self.biz = Business.objects.create(
            owner=self.owner, name="Revoke Test Biz", trade_type=TradeType.GROCERY,
            address="Street 1", district="Hyderabad", pincode="500001"
        )
        self.inst = Instrument.objects.create(
            business=self.biz, category=Category.COUNTER_SCALE,
            make="Avery", model_no="AT-1", serial_no="REV-01",
            max_capacity=Decimal("15"), unit=Unit.KG,
            scale_interval_e=Decimal("0.005"), accuracy_class=AccuracyClass.CLASS_III
        )
        self.req = VerificationRequest.objects.create(
            instrument=self.inst, requested_by=self.owner,
            preferred_date="2026-11-01", status=RequestStatus.PASSED,
            inspector=self.inspector
        )
        self.inspection = Inspection.objects.create(
            request=self.req, inspector=self.inspector,
            zero_ok=True, result=InspectionResult.PASS
        )
        self.cert = issue_certificate(self.inspection, actor=self.inspector)
        self.revoke_url = reverse("certificate_revoke", kwargs={"number": self.cert.number})

    def test_admin_can_access_revoke_page_get(self):
        self.client.login(username="admin_revoker", password="password123")
        response = self.client.get(self.revoke_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cert.number)

    def test_admin_revoke_success(self):
        self.client.login(username="admin_revoker", password="password123")
        response = self.client.post(self.revoke_url, {"reason": "Fraudulent seal detected"})
        self.assertRedirects(response, reverse("public_token_verify", kwargs={"token": self.cert.token}))
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.state, "REVOKED")
        self.assertEqual(self.cert.revoked_reason, "Fraudulent seal detected")
        self.assertEqual(self.cert.revoked_by, self.admin)

    def test_admin_revoke_requires_reason(self):
        self.client.login(username="admin_revoker", password="password123")
        response = self.client.post(self.revoke_url, {"reason": "   "})
        self.assertEqual(response.status_code, 200)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.state, "VALID")
        self.assertContains(response, "A revocation reason is required")

    def test_owner_cannot_access_revoke_view(self):
        self.client.login(username="owner_revoker", password="password123")
        response = self.client.get(self.revoke_url)
        self.assertEqual(response.status_code, 403)

    def test_inspector_cannot_access_revoke_view(self):
        self.client.login(username="insp_revoker", password="password123")
        response = self.client.get(self.revoke_url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_from_revoke_view(self):
        response = self.client.get(self.revoke_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class SendExpiryRemindersCommandTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_reminder",
            email="owner.reminder@example.com",
            password="password123",
            role=User.Role.OWNER,
        )
        self.biz = Business.objects.create(
            owner=self.owner,
            name="Reminder Kirana Store",
            trade_type=TradeType.GROCERY,
            address="Main Bazaar",
            district="Hyderabad",
            pincode="500001",
        )
        self.inspector = User.objects.create_user(
            username="insp_reminder", password="password123", role=User.Role.INSPECTOR
        )
        self.today = timezone.now().date()

        def make_cert(serial, valid_until, is_revoked=False):
            inst = Instrument.objects.create(
                business=self.biz,
                category=Category.COUNTER_SCALE,
                make="Essae",
                model_no="E-1",
                serial_no=serial,
                max_capacity=Decimal("15"),
                unit=Unit.KG,
                scale_interval_e=Decimal("0.005"),
                accuracy_class=AccuracyClass.CLASS_III,
            )
            req = VerificationRequest.objects.create(
                instrument=inst,
                requested_by=self.owner,
                preferred_date=self.today,
                status=RequestStatus.PASSED,
                inspector=self.inspector,
            )
            insp = Inspection.objects.create(
                request=req,
                inspector=self.inspector,
                zero_ok=True,
                result=InspectionResult.PASS,
            )
            cert = Certificate.objects.create(
                inspection=insp,
                number=f"TOLA-REM-{serial}",
                issued_on=self.today - datetime.timedelta(days=335),
                valid_until=valid_until,
            )
            if is_revoked:
                cert.revoked_at = timezone.now()
                cert.revoked_reason = "Revoked for test"
                cert.save()
            return cert

        # 1. Exactly 30 days remaining -> SHOULD send reminder
        self.cert_30d = make_cert("REM-30D", self.today + datetime.timedelta(days=30))
        # 2. Exactly 7 days remaining -> SHOULD send reminder
        self.cert_7d = make_cert("REM-7D", self.today + datetime.timedelta(days=7))
        # 3. 29 days remaining -> Should NOT send
        self.cert_29d = make_cert("REM-29D", self.today + datetime.timedelta(days=29))
        # 4. 8 days remaining -> Should NOT send
        self.cert_8d = make_cert("REM-8D", self.today + datetime.timedelta(days=8))
        # 5. Expired 5 days ago -> Should NOT send
        self.cert_expired = make_cert("REM-EXP", self.today - datetime.timedelta(days=5))
        # 6. Exactly 30 days remaining but REVOKED -> Should NOT send
        self.cert_revoked_30d = make_cert("REM-REV-30D", self.today + datetime.timedelta(days=30), is_revoked=True)

    def test_reminders_sent_only_for_exact_30_and_7_days(self):
        out = StringIO()
        call_command("send_expiry_reminders", stdout=out)

        # Only 2 emails should be sent: cert_30d and cert_7d
        self.assertEqual(len(mail.outbox), 2)

        subjects = [m.subject for m in mail.outbox]
        self.assertTrue(any(self.cert_30d.number in s and "30 days" in s for s in subjects))
        self.assertTrue(any(self.cert_7d.number in s and "7 days" in s for s in subjects))

        for msg in mail.outbox:
            self.assertEqual(msg.to, ["owner.reminder@example.com"])
            self.assertIn("Legal Metrology Act, 2009", msg.body)
            self.assertIn("Reminder Kirana Store", msg.body)

    def test_dry_run_does_not_send_emails(self):
        out = StringIO()
        call_command("send_expiry_reminders", "--dry-run", stdout=out)
        self.assertEqual(len(mail.outbox), 0)
        self.assertIn("[DRY RUN]", out.getvalue())
        self.assertIn("Simulated 2 certificate expiry reminder(s)", out.getvalue())
