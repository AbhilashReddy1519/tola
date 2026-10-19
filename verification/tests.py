from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from registry.models import AccuracyClass, Business, Category, Instrument, TradeType, Unit
from .models import Inspection, InspectionResult, ReadingKind, RequestStatus, StatusEvent, TestReading, VerificationRequest
from .rules import evaluate_reading, is_inspection_passing, mpe_for
from .services import InvalidTransitionError, transition

User = get_user_model()


class StateMachineTransitionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_sm", password="password123", role=User.Role.OWNER
        )
        self.business = Business.objects.create(
            owner=self.owner, name="SM Biz", trade_type=TradeType.GROCERY,
            address="Addr", district="Dist", pincode="500001"
        )
        self.instrument = Instrument.objects.create(
            business=self.business, category=Category.COUNTER_SCALE,
            make="Avery", model_no="M1", serial_no="SM-01",
            max_capacity=Decimal("15"), unit=Unit.KG,
            scale_interval_e=Decimal("0.005"), accuracy_class=AccuracyClass.CLASS_III
        )
        self.req = VerificationRequest.objects.create(
            instrument=self.instrument,
            requested_by=self.owner,
            preferred_date="2026-11-01",
            status=RequestStatus.SUBMITTED,
        )

    def test_allowed_transitions(self):
        # SUBMITTED -> ASSIGNED
        ev1 = transition(self.req, RequestStatus.ASSIGNED, actor=self.owner, note="Assigned")
        self.assertEqual(self.req.status, RequestStatus.ASSIGNED)
        self.assertEqual(ev1.from_status, RequestStatus.SUBMITTED)
        self.assertEqual(ev1.to_status, RequestStatus.ASSIGNED)
        self.assertEqual(StatusEvent.objects.filter(request=self.req).count(), 1)

        # ASSIGNED -> PASSED
        ev2 = transition(self.req, RequestStatus.PASSED, actor=self.owner, note="Passed")
        self.assertEqual(self.req.status, RequestStatus.PASSED)
        self.assertEqual(ev2.to_status, RequestStatus.PASSED)

        # PASSED -> CERTIFIED
        ev3 = transition(self.req, RequestStatus.CERTIFIED, actor=self.owner, note="Certified")
        self.assertEqual(self.req.status, RequestStatus.CERTIFIED)
        self.assertEqual(ev3.to_status, RequestStatus.CERTIFIED)

    def test_assigned_to_failed_transition(self):
        transition(self.req, RequestStatus.ASSIGNED, actor=self.owner)
        ev = transition(self.req, RequestStatus.FAILED, actor=self.owner, note="Failed inspection")
        self.assertEqual(self.req.status, RequestStatus.FAILED)
        self.assertEqual(ev.to_status, RequestStatus.FAILED)

    def test_cancellation_transitions(self):
        # SUBMITTED -> CANCELLED
        transition(self.req, RequestStatus.CANCELLED, actor=self.owner, note="Cancelled")
        self.assertEqual(self.req.status, RequestStatus.CANCELLED)

    def test_disallowed_transitions_raise_error(self):
        # Direct SUBMITTED -> PASSED is forbidden
        with self.assertRaises(InvalidTransitionError):
            transition(self.req, RequestStatus.PASSED, actor=self.owner)

        # Direct SUBMITTED -> CERTIFIED is forbidden
        with self.assertRaises(InvalidTransitionError):
            transition(self.req, RequestStatus.CERTIFIED, actor=self.owner)

        # Cancelled terminal state cannot transition anywhere
        transition(self.req, RequestStatus.CANCELLED, actor=self.owner)
        with self.assertRaises(InvalidTransitionError):
            transition(self.req, RequestStatus.ASSIGNED, actor=self.owner)


class PermittedErrorRulesTests(TestCase):
    def test_mpe_boundaries(self):
        e = Decimal("0.01")  # 10g

        # At load = 2.0 (m = 200 e <= 500): MPE = 0.5 e = 0.005
        self.assertEqual(mpe_for(load=Decimal("2.0"), e=e), Decimal("0.0050"))

        # Exact boundary at 500 e (load = 5.0): MPE = 0.5 e = 0.005
        self.assertEqual(mpe_for(load=Decimal("5.0"), e=e), Decimal("0.0050"))

        # Above 500 e to 2000 e (load = 5.01, m = 501 e): MPE = 1.0 e = 0.010
        self.assertEqual(mpe_for(load=Decimal("5.01"), e=e), Decimal("0.0100"))

        # Exact boundary at 2000 e (load = 20.0): MPE = 1.0 e = 0.010
        self.assertEqual(mpe_for(load=Decimal("20.0"), e=e), Decimal("0.0100"))

        # Above 2000 e to 10000 e (load = 20.01, m = 2001 e): MPE = 1.5 e = 0.015
        self.assertEqual(mpe_for(load=Decimal("20.01"), e=e), Decimal("0.0150"))

        # Exact boundary at 10000 e (load = 100.0): MPE = 1.5 e = 0.015
        self.assertEqual(mpe_for(load=Decimal("100.0"), e=e), Decimal("0.0150"))

    def test_evaluate_reading(self):
        e = Decimal("0.01")
        # Load = 10 (m = 1000, MPE = 0.01)
        # Indication = 10.008 -> error = +0.008 <= 0.01 -> passes
        res_pass = evaluate_reading(load=Decimal("10.0"), indication=Decimal("10.008"), e=e)
        self.assertTrue(res_pass["within_limit"])
        self.assertEqual(res_pass["error"], Decimal("0.008"))

        # Indication = 10.015 -> error = +0.015 > 0.01 -> fails
        res_fail = evaluate_reading(load=Decimal("10.0"), indication=Decimal("10.015"), e=e)
        self.assertFalse(res_fail["within_limit"])

    def test_zero_ok_false_forces_fail(self):
        e = Decimal("0.01")
        perfect_reading = evaluate_reading(load=Decimal("10.0"), indication=Decimal("10.0"), e=e)
        self.assertTrue(perfect_reading["within_limit"])

        # Even with 100% accurate readings, zero_ok False forces inspection FAIL
        self.assertFalse(is_inspection_passing(zero_ok=False, readings=[perfect_reading]))
        self.assertTrue(is_inspection_passing(zero_ok=True, readings=[perfect_reading]))


class VerificationWorkflowPermissionsTests(TestCase):
    def setUp(self):
        # Owner A
        self.owner_a = User.objects.create_user(
            username="owner_a_flow", password="password123", role=User.Role.OWNER
        )
        self.biz_a = Business.objects.create(
            owner=self.owner_a, name="Biz A", trade_type=TradeType.GROCERY,
            address="Addr", district="Dist", pincode="500001"
        )
        self.inst_a = Instrument.objects.create(
            business=self.biz_a, category=Category.COUNTER_SCALE,
            make="Avery", model_no="M1", serial_no="INST-A",
            max_capacity=Decimal("10"), unit=Unit.KG,
            scale_interval_e=Decimal("0.002"), accuracy_class=AccuracyClass.CLASS_III
        )

        # Owner B
        self.owner_b = User.objects.create_user(
            username="owner_b_flow", password="password123", role=User.Role.OWNER
        )
        self.biz_b = Business.objects.create(
            owner=self.owner_b, name="Biz B", trade_type=TradeType.GROCERY,
            address="Addr B", district="Dist B", pincode="500002"
        )
        self.inst_b = Instrument.objects.create(
            business=self.biz_b, category=Category.PLATFORM_SCALE,
            make="Crown", model_no="M2", serial_no="INST-B",
            max_capacity=Decimal("50"), unit=Unit.KG,
            scale_interval_e=Decimal("0.01"), accuracy_class=AccuracyClass.CLASS_III
        )

        # Inspector 1 and 2
        self.inspector_1 = User.objects.create_user(
            username="inspector_1", password="password123", role=User.Role.INSPECTOR
        )
        self.inspector_2 = User.objects.create_user(
            username="inspector_2", password="password123", role=User.Role.INSPECTOR
        )

        # Admin
        self.admin = User.objects.create_user(
            username="admin_flow", password="password123", role=User.Role.ADMIN
        )

        # Request for Instrument A
        self.req_a = VerificationRequest.objects.create(
            instrument=self.inst_a,
            requested_by=self.owner_a,
            preferred_date="2026-11-10",
            status=RequestStatus.SUBMITTED,
        )

    def test_owner_cannot_request_verification_for_other_instrument(self):
        self.client.login(username="owner_a_flow", password="password123")
        # Owner A attempts to file request choosing Instrument B (owned by Owner B)
        data = {
            "instrument": self.inst_b.pk,
            "preferred_date": "2026-11-20",
            "notes": "Trying to verify another's instrument",
        }
        response = self.client.post(reverse("owner_request_create"), data)
        # Form field validation scopes choices to owner A's instruments, rejecting foreign pk
        self.assertFalse(VerificationRequest.objects.filter(instrument=self.inst_b).exists())

    def test_inspector_cannot_open_unassigned_request(self):
        self.client.login(username="inspector_1", password="password123")
        # Request A is currently SUBMITTED, unassigned
        response = self.client.get(
            reverse("inspector_inspect", kwargs={"pk": self.req_a.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_inspector_cannot_open_request_assigned_to_another(self):
        # Assign Request A to Inspector 2
        self.req_a.inspector = self.inspector_2
        self.req_a.status = RequestStatus.ASSIGNED
        self.req_a.save()

        # Inspector 1 logs in and tries to inspect
        self.client.login(username="inspector_1", password="password123")
        response = self.client.get(
            reverse("inspector_inspect", kwargs={"pk": self.req_a.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_assignment_calls_transition(self):
        self.client.login(username="admin_flow", password="password123")
        data = {
            "inspector": self.inspector_1.pk,
            "notes": "Assigned to Inspector 1 for priority visit",
        }
        response = self.client.post(
            reverse("admin_request_assign", kwargs={"pk": self.req_a.pk}), data
        )
        self.assertEqual(response.status_code, 302)
        self.req_a.refresh_from_db()
        self.assertEqual(self.req_a.status, RequestStatus.ASSIGNED)
        self.assertEqual(self.req_a.inspector, self.inspector_1)
        self.assertTrue(StatusEvent.objects.filter(request=self.req_a, to_status=RequestStatus.ASSIGNED).exists())

    def test_inspection_submission_pass(self):
        # Assign to inspector 1
        self.req_a.inspector = self.inspector_1
        self.req_a.status = RequestStatus.ASSIGNED
        self.req_a.save()

        self.client.login(username="inspector_1", password="password123")
        post_data = {
            "zero_ok": "true",
            "remarks": "Calibrated with certified test weights.",
            "kind[]": ["ACCURACY", "REPEATABILITY"],
            "test_load[]": ["5.0", "10.0"],
            "indication[]": ["5.001", "10.001"],  # Well within MPE
        }
        response = self.client.post(
            reverse("inspector_inspect", kwargs={"pk": self.req_a.pk}), post_data
        )
        self.assertEqual(response.status_code, 302)
        self.req_a.refresh_from_db()
        self.assertEqual(self.req_a.status, RequestStatus.CERTIFIED)
        self.assertTrue(hasattr(self.req_a, "inspection"))
        self.assertEqual(self.req_a.inspection.result, InspectionResult.PASS)
        self.assertEqual(self.req_a.inspection.readings.count(), 2)
        self.assertTrue(hasattr(self.req_a.inspection, "certificate"))

    def test_inspection_submission_fail(self):
        # Assign to inspector 1
        self.req_a.inspector = self.inspector_1
        self.req_a.status = RequestStatus.ASSIGNED
        self.req_a.save()

        self.client.login(username="inspector_1", password="password123")
        post_data = {
            "zero_ok": "true",
            "remarks": "Exceeded maximum permissible error.",
            "kind[]": ["ACCURACY"],
            "test_load[]": ["5.0"],
            "indication[]": ["5.050"],  # Error = 0.050, MPE = 0.005 -> FAILS
        }
        response = self.client.post(
            reverse("inspector_inspect", kwargs={"pk": self.req_a.pk}), post_data
        )
        self.assertEqual(response.status_code, 302)
        self.req_a.refresh_from_db()
        self.assertEqual(self.req_a.status, RequestStatus.FAILED)
        self.assertEqual(self.req_a.inspection.result, InspectionResult.FAIL)
