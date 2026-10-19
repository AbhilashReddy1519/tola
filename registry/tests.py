from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection, IntegrityError, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import AccuracyClass, Business, Category, Instrument, TradeType, Unit

User = get_user_model()


class RegistryModelValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_a",
            password="password123",
            role=User.Role.OWNER,
        )
        self.business = Business.objects.create(
            owner=self.owner,
            name="Ramesh Kirana Store",
            trade_type=TradeType.GROCERY,
            address="12 Market Yard",
            district="Hyderabad",
            pincode="500001",
        )

    def test_capacity_must_be_strictly_greater_than_zero(self):
        # Positive capacity succeeds
        inst = Instrument(
            business=self.business,
            category=Category.COUNTER_SCALE,
            make="Avery",
            model_no="AT-100",
            serial_no="SN-001",
            max_capacity=Decimal("15.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0050"),
            accuracy_class=AccuracyClass.CLASS_III,
        )
        inst.full_clean()
        inst.save()

        # Zero capacity raises ValidationError
        inst_zero = Instrument(
            business=self.business,
            category=Category.COUNTER_SCALE,
            make="Avery",
            model_no="AT-100",
            serial_no="SN-002",
            max_capacity=Decimal("0"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0050"),
            accuracy_class=AccuracyClass.CLASS_III,
        )
        with self.assertRaises(ValidationError):
            inst_zero.full_clean()

        # Negative capacity raises ValidationError
        inst_negative = Instrument(
            business=self.business,
            category=Category.COUNTER_SCALE,
            make="Avery",
            model_no="AT-100",
            serial_no="SN-003",
            max_capacity=Decimal("-5.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0050"),
            accuracy_class=AccuracyClass.CLASS_III,
        )
        with self.assertRaises(ValidationError):
            inst_negative.full_clean()

    def test_serial_uniqueness_per_business(self):
        Instrument.objects.create(
            business=self.business,
            category=Category.COUNTER_SCALE,
            make="Avery",
            model_no="AT-100",
            serial_no="DUP-SERIAL-1",
            max_capacity=Decimal("30.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0100"),
            accuracy_class=AccuracyClass.CLASS_III,
        )

        # Duplicate serial for SAME business raises IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Instrument.objects.create(
                    business=self.business,
                    category=Category.PLATFORM_SCALE,
                    make="Crown",
                    model_no="CR-200",
                    serial_no="DUP-SERIAL-1",
                    max_capacity=Decimal("100.0000"),
                    unit=Unit.KG,
                    scale_interval_e=Decimal("0.0500"),
                    accuracy_class=AccuracyClass.CLASS_III,
                )

        # Same serial for DIFFERENT business succeeds
        owner_b = User.objects.create_user(
            username="owner_b",
            password="password123",
            role=User.Role.OWNER,
        )
        business_b = Business.objects.create(
            owner=owner_b,
            name="Priya Jewellers",
            trade_type=TradeType.JEWELLERY,
            address="45 MG Road",
            district="Hyderabad",
            pincode="500003",
        )
        diff_inst = Instrument.objects.create(
            business=business_b,
            category=Category.COUNTER_SCALE,
            make="Crown",
            model_no="CR-200",
            serial_no="DUP-SERIAL-1",
            max_capacity=Decimal("10.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0010"),
            accuracy_class=AccuracyClass.CLASS_II,
        )
        self.assertIsNotNone(diff_inst.pk)


class ObjectScopingAndPermissionsTests(TestCase):
    def setUp(self):
        # Owner A and business
        self.owner_a = User.objects.create_user(
            username="owner_alpha",
            password="password123",
            role=User.Role.OWNER,
        )
        self.business_a = Business.objects.create(
            owner=self.owner_a,
            name="Alpha Traders",
            trade_type=TradeType.GROCERY,
            address="10 Alpha St",
            district="North",
            pincode="100001",
        )
        self.inst_a = Instrument.objects.create(
            business=self.business_a,
            category=Category.COUNTER_SCALE,
            make="ScaleCorp",
            model_no="SC-1",
            serial_no="ALPHA-001",
            max_capacity=Decimal("25.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0050"),
            accuracy_class=AccuracyClass.CLASS_III,
        )

        # Owner B and business
        self.owner_b = User.objects.create_user(
            username="owner_beta",
            password="password123",
            role=User.Role.OWNER,
        )
        self.business_b = Business.objects.create(
            owner=self.owner_b,
            name="Beta Provisions",
            trade_type=TradeType.GROCERY,
            address="20 Beta Rd",
            district="South",
            pincode="200002",
        )
        self.inst_b = Instrument.objects.create(
            business=self.business_b,
            category=Category.PLATFORM_SCALE,
            make="WeighTech",
            model_no="WT-50",
            serial_no="BETA-999",
            max_capacity=Decimal("50.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0100"),
            accuracy_class=AccuracyClass.CLASS_III,
        )

        # Inspector user
        self.inspector = User.objects.create_user(
            username="inspector_bob",
            password="password123",
            role=User.Role.INSPECTOR,
        )

    def test_owner_a_gets_404_for_owner_b_instrument_detail(self):
        self.client.login(username="owner_alpha", password="password123")
        response = self.client.get(
            reverse("instrument_detail", kwargs={"pk": self.inst_b.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_owner_a_gets_404_for_owner_b_instrument_edit(self):
        self.client.login(username="owner_alpha", password="password123")
        response = self.client.get(
            reverse("instrument_edit", kwargs={"pk": self.inst_b.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_instrument_list_strictly_scoped(self):
        self.client.login(username="owner_alpha", password="password123")
        response = self.client.get(reverse("instrument_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ALPHA-001")
        self.assertNotContains(response, "BETA-999")

    def test_inspector_cannot_access_instrument_list(self):
        self.client.login(username="inspector_bob", password="password123")
        response = self.client.get(reverse("instrument_list"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_from_instrument_list(self):
        response = self.client.get(reverse("instrument_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class InstrumentCRUDTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_crud",
            password="password123",
            role=User.Role.OWNER,
        )
        self.business = Business.objects.create(
            owner=self.owner,
            name="CRUD Enterprise",
            trade_type=TradeType.WEIGHBRIDGE,
            address="Highway 44",
            district="Central",
            pincode="300003",
        )
        self.client.login(username="owner_crud", password="password123")

    def test_create_instrument_success(self):
        data = {
            "category": Category.WEIGHBRIDGE,
            "make": "Essae",
            "model_no": "WB-50000",
            "serial_no": "ES-WB-101",
            "max_capacity": "50000.0000",
            "unit": Unit.KG,
            "scale_interval_e": "10.0000",
            "accuracy_class": AccuracyClass.CLASS_III,
            "installed_on": "2026-01-15",
        }
        response = self.client.post(reverse("instrument_create"), data)
        self.assertEqual(response.status_code, 302)
        inst = Instrument.objects.get(serial_no="ES-WB-101")
        self.assertEqual(inst.business, self.business)
        self.assertEqual(inst.max_capacity, Decimal("50000.0000"))

    def test_edit_instrument_success(self):
        inst = Instrument.objects.create(
            business=self.business,
            category=Category.COUNTER_SCALE,
            make="OldMake",
            model_no="OldModel",
            serial_no="EDIT-ME",
            max_capacity=Decimal("10.0000"),
            unit=Unit.KG,
            scale_interval_e=Decimal("0.0010"),
            accuracy_class=AccuracyClass.CLASS_III,
        )
        data = {
            "category": Category.COUNTER_SCALE,
            "make": "NewMake",
            "model_no": "NewModel",
            "serial_no": "EDIT-ME",
            "max_capacity": "20.0000",
            "unit": Unit.KG,
            "scale_interval_e": "0.0020",
            "accuracy_class": AccuracyClass.CLASS_III,
        }
        response = self.client.post(
            reverse("instrument_edit", kwargs={"pk": inst.pk}), data
        )
        self.assertEqual(response.status_code, 302)
        inst.refresh_from_db()
        self.assertEqual(inst.make, "NewMake")
        self.assertEqual(inst.max_capacity, Decimal("20.0000"))


class InstrumentListQueryCountTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="query_owner", password="password123", role=User.Role.OWNER
        )
        self.biz = Business.objects.create(
            owner=self.owner, name="Query Test Biz", trade_type=TradeType.GROCERY,
            address="Addr", district="Dist", pincode="500001"
        )
        for i in range(5):
            Instrument.objects.create(
                business=self.biz,
                category=Category.COUNTER_SCALE,
                make="Essae",
                model_no="E-100",
                serial_no=f"Q-INST-{i:03d}",
                max_capacity=Decimal("30"),
                unit=Unit.KG,
                scale_interval_e=Decimal("0.01"),
                accuracy_class=AccuracyClass.CLASS_III,
            )

    def test_instrument_list_query_count_constant(self):
        self.client.login(username="query_owner", password="password123")
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse("instrument_list"))
        self.assertEqual(response.status_code, 200)
        # Constant query count: session, user, business, instruments, prefetched requests, prefetched inspections
        self.assertLessEqual(len(ctx.captured_queries), 6)
