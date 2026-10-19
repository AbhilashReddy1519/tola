import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from certificates.models import Certificate
from registry.models import AccuracyClass, Business, Category, Instrument, TradeType, Unit
from verification.models import (
    Inspection,
    InspectionResult,
    ReadingKind,
    RequestStatus,
    StatusEvent,
    TestReading,
    VerificationRequest,
)

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Seeds the database with realistic Legal Metrology demonstration data: "
        "1 admin, 2 inspectors, 5 business owners, 25 instruments, requests in every status, "
        "and certificates in VALID, EXPIRING, EXPIRED, and REVOKED states. Fully idempotent."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding Tola Legal Metrology Demo Data ==="))

        with transaction.atomic():
            users = self._seed_users()
            businesses = self._seed_businesses(users)
            instruments = self._seed_instruments(businesses)
            self._seed_requests_and_certificates(users, instruments)

        self._print_credentials(users)
        self.stdout.write(self.style.SUCCESS("Demo database successfully seeded and verified!\n"))

    def _seed_users(self):
        user_specs = [
            # Admin
            {
                "username": "admin",
                "email": "admin@tola.local",
                "password": "AdminPassword123!",
                "role": User.Role.ADMIN,
                "first_name": "Sanjay",
                "last_name": "Verma",
                "phone": "+91 90000 00001",
                "is_staff": True,
                "is_superuser": True,
            },
            # Inspectors
            {
                "username": "inspector_rajesh",
                "email": "rajesh.inspector@tola.local",
                "password": "InspectorPassword123!",
                "role": User.Role.INSPECTOR,
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "phone": "+91 98765 43210",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "inspector_anita",
                "email": "anita.inspector@tola.local",
                "password": "InspectorPassword123!",
                "role": User.Role.INSPECTOR,
                "first_name": "Anita",
                "last_name": "Sharma",
                "phone": "+91 98765 43220",
                "is_staff": False,
                "is_superuser": False,
            },
            # Owners
            {
                "username": "owner_ramesh",
                "email": "ramesh.grocers@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "first_name": "Ramesh",
                "last_name": "Patel",
                "phone": "+91 98765 43211",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "owner_priya",
                "email": "priya.jewellers@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "first_name": "Priya",
                "last_name": "Sundaram",
                "phone": "+91 98765 43212",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "owner_manpreet",
                "email": "manpreet.weigh@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "first_name": "Manpreet",
                "last_name": "Singh",
                "phone": "+91 98765 43213",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "owner_fatima",
                "email": "fatima.oilmills@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "first_name": "Fatima",
                "last_name": "Begum",
                "phone": "+91 98765 43214",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "owner_vikram",
                "email": "vikram.mandi@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "first_name": "Vikram",
                "last_name": "Desai",
                "phone": "+91 98765 43215",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        seeded_users = {}
        for spec in user_specs:
            user, _ = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "role": spec["role"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "phone": spec["phone"],
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                },
            )
            user.set_password(spec["password"])
            user.role = spec["role"]
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.email = spec["email"]
            user.phone = spec["phone"]
            user.is_staff = spec["is_staff"]
            user.is_superuser = spec["is_superuser"]
            user.save()
            seeded_users[spec["username"]] = user

        return seeded_users

    def _seed_businesses(self, users):
        biz_specs = [
            {
                "owner": users["owner_ramesh"],
                "name": "Sri Lakshmi Kirana & General Stores",
                "trade_type": TradeType.GROCERY,
                "address": "Shop 12-14, Old Grain Market, Koti",
                "district": "Hyderabad",
                "pincode": "500001",
                "licence_no": "LM-TS-HYD-2024-00812",
            },
            {
                "owner": users["owner_priya"],
                "name": "Sundaram Jewellers & Bullion Merchants",
                "trade_type": TradeType.JEWELLERY,
                "address": "45 Sarafa Bazaar, Hanamkonda",
                "district": "Warangal",
                "pincode": "506001",
                "licence_no": "LM-TS-WGL-2023-00194",
            },
            {
                "owner": users["owner_manpreet"],
                "name": "Punjab Highway Weighbridge & Freight Terminal",
                "trade_type": TradeType.WEIGHBRIDGE,
                "address": "NH-44 Bypass, Industrial Area",
                "district": "Nizamabad",
                "pincode": "503001",
                "licence_no": "LM-TS-NZB-2022-00455",
            },
            {
                "owner": users["owner_fatima"],
                "name": "Deccan Oil Mills & Bulk Traders",
                "trade_type": TradeType.OTHER,
                "address": "88 Industrial Estate, Jagtial Road",
                "district": "Karimnagar",
                "pincode": "505001",
                "licence_no": "LM-TS-KRN-2024-00318",
            },
            {
                "owner": users["owner_vikram"],
                "name": "Desai Agro Provisions & Mandi Yard",
                "trade_type": TradeType.GROCERY,
                "address": "Plot 23, APMC Yard, Wyra Road",
                "district": "Khammam",
                "pincode": "507001",
                "licence_no": "LM-TS-KHM-2023-00621",
            },
        ]

        seeded_businesses = {}
        for spec in biz_specs:
            biz, _ = Business.objects.get_or_create(
                owner=spec["owner"],
                defaults=spec,
            )
            for field, val in spec.items():
                setattr(biz, field, val)
            biz.save()
            seeded_businesses[spec["owner"].username] = biz

        return seeded_businesses

    def _seed_instruments(self, businesses):
        # 5 instruments per business = 25 instruments total
        inst_specs = [
            # Business 1: Sri Lakshmi Kirana (owner_ramesh) - 5 instruments
            {
                "business": businesses["owner_ramesh"],
                "category": Category.COUNTER_SCALE,
                "make": "Essae",
                "model_no": "DS-215",
                "serial_no": "LK-CS-001",
                "max_capacity": Decimal("15.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0050"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_ramesh"],
                "category": Category.COUNTER_SCALE,
                "make": "Avery",
                "model_no": "Berkel-30",
                "serial_no": "LK-CS-002",
                "max_capacity": Decimal("30.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0100"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_ramesh"],
                "category": Category.PLATFORM_SCALE,
                "make": "Essae",
                "model_no": "PR-150",
                "serial_no": "LK-PS-003",
                "max_capacity": Decimal("150.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0500"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_ramesh"],
                "category": Category.COUNTER_SCALE,
                "make": "Crown",
                "model_no": "CR-10",
                "serial_no": "LK-CS-004",
                "max_capacity": Decimal("10.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0020"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_ramesh"],
                "category": Category.PLATFORM_SCALE,
                "make": "Crown",
                "model_no": "CR-300",
                "serial_no": "LK-PS-005",
                "max_capacity": Decimal("300.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.1000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },

            # Business 2: Sundaram Jewellers (owner_priya) - 5 instruments
            {
                "business": businesses["owner_priya"],
                "category": Category.COUNTER_SCALE,
                "make": "Sartorius",
                "model_no": "ENTRIS-64",
                "serial_no": "SJ-GB-001",
                "max_capacity": Decimal("0.5000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0001"),
                "accuracy_class": AccuracyClass.CLASS_I,
            },
            {
                "business": businesses["owner_priya"],
                "category": Category.COUNTER_SCALE,
                "make": "Sartorius",
                "model_no": "BCE-2202",
                "serial_no": "SJ-GB-002",
                "max_capacity": Decimal("2.2000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0010"),
                "accuracy_class": AccuracyClass.CLASS_II,
            },
            {
                "business": businesses["owner_priya"],
                "category": Category.COUNTER_SCALE,
                "make": "Essae",
                "model_no": "JW-5",
                "serial_no": "SJ-CS-003",
                "max_capacity": Decimal("5.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0010"),
                "accuracy_class": AccuracyClass.CLASS_II,
            },
            {
                "business": businesses["owner_priya"],
                "category": Category.COUNTER_SCALE,
                "make": "Avery",
                "model_no": "PREC-1",
                "serial_no": "SJ-CS-004",
                "max_capacity": Decimal("1.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0002"),
                "accuracy_class": AccuracyClass.CLASS_II,
            },
            {
                "business": businesses["owner_priya"],
                "category": Category.COUNTER_SCALE,
                "make": "Sansui",
                "model_no": "GOLD-500",
                "serial_no": "SJ-CS-005",
                "max_capacity": Decimal("0.5000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0001"),
                "accuracy_class": AccuracyClass.CLASS_I,
            },

            # Business 3: Punjab Highway Weighbridge (owner_manpreet) - 5 instruments
            {
                "business": businesses["owner_manpreet"],
                "category": Category.WEIGHBRIDGE,
                "make": "Fairbanks",
                "model_no": "TITAN-50T",
                "serial_no": "PHW-WB-001",
                "max_capacity": Decimal("50000.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("10.0000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_manpreet"],
                "category": Category.WEIGHBRIDGE,
                "make": "Avery Weigh-Tronix",
                "model_no": "BRIDGE-60",
                "serial_no": "PHW-WB-002",
                "max_capacity": Decimal("60000.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("20.0000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_manpreet"],
                "category": Category.PLATFORM_SCALE,
                "make": "Essae",
                "model_no": "WB-IN-500",
                "serial_no": "PHW-PS-003",
                "max_capacity": Decimal("500.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.1000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_manpreet"],
                "category": Category.PLATFORM_SCALE,
                "make": "Crown",
                "model_no": "HEAVY-1000",
                "serial_no": "PHW-PS-004",
                "max_capacity": Decimal("1000.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.2000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_manpreet"],
                "category": Category.WEIGHBRIDGE,
                "make": "Essae",
                "model_no": "TRUCK-40T",
                "serial_no": "PHW-WB-005",
                "max_capacity": Decimal("40000.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("10.0000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },

            # Business 4: Deccan Oil Mills (owner_fatima) - 5 instruments
            {
                "business": businesses["owner_fatima"],
                "category": Category.CAPACITY_MEASURE,
                "make": "Standard Measure Co",
                "model_no": "CONICAL-20L",
                "serial_no": "DOT-CM-001",
                "max_capacity": Decimal("20.0000"),
                "unit": Unit.L,
                "scale_interval_e": Decimal("0.0200"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_fatima"],
                "category": Category.CAPACITY_MEASURE,
                "make": "National Measures",
                "model_no": "CYL-5L",
                "serial_no": "DOT-CM-002",
                "max_capacity": Decimal("5.0000"),
                "unit": Unit.L,
                "scale_interval_e": Decimal("0.0100"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_fatima"],
                "category": Category.PLATFORM_SCALE,
                "make": "Avery",
                "model_no": "DRUM-300",
                "serial_no": "DOT-PS-003",
                "max_capacity": Decimal("300.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.1000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_fatima"],
                "category": Category.COUNTER_SCALE,
                "make": "Essae",
                "model_no": "OIL-15",
                "serial_no": "DOT-CS-004",
                "max_capacity": Decimal("15.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0050"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_fatima"],
                "category": Category.CAPACITY_MEASURE,
                "make": "Standard Measure Co",
                "model_no": "CONICAL-50L",
                "serial_no": "DOT-CM-005",
                "max_capacity": Decimal("50.0000"),
                "unit": Unit.L,
                "scale_interval_e": Decimal("0.0500"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },

            # Business 5: Desai Agro Provisions (owner_vikram) - 5 instruments
            {
                "business": businesses["owner_vikram"],
                "category": Category.PLATFORM_SCALE,
                "make": "Avery",
                "model_no": "BAG-500",
                "serial_no": "DAG-PS-001",
                "max_capacity": Decimal("500.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.1000"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_vikram"],
                "category": Category.PLATFORM_SCALE,
                "make": "Crown",
                "model_no": "MANDI-300",
                "serial_no": "DAG-PS-002",
                "max_capacity": Decimal("300.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0500"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_vikram"],
                "category": Category.LENGTH_MEASURE,
                "make": "Standard Metrology",
                "model_no": "STEEL-METER",
                "serial_no": "DAG-LM-003",
                "max_capacity": Decimal("1.0000"),
                "unit": Unit.M,
                "scale_interval_e": Decimal("0.0010"),
                "accuracy_class": AccuracyClass.CLASS_II,
            },
            {
                "business": businesses["owner_vikram"],
                "category": Category.COUNTER_SCALE,
                "make": "Essae",
                "model_no": "AGRO-30",
                "serial_no": "DAG-CS-004",
                "max_capacity": Decimal("30.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0100"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
            {
                "business": businesses["owner_vikram"],
                "category": Category.COUNTER_SCALE,
                "make": "Sansui",
                "model_no": "GRAIN-20",
                "serial_no": "DAG-CS-005",
                "max_capacity": Decimal("20.0000"),
                "unit": Unit.KG,
                "scale_interval_e": Decimal("0.0050"),
                "accuracy_class": AccuracyClass.CLASS_III,
            },
        ]

        seeded_instruments = {}
        for spec in inst_specs:
            inst, _ = Instrument.objects.get_or_create(
                business=spec["business"],
                serial_no=spec["serial_no"],
                defaults=spec,
            )
            for field, val in spec.items():
                setattr(inst, field, val)
            inst.save()
            seeded_instruments[spec["serial_no"]] = inst

        return seeded_instruments

    def _seed_requests_and_certificates(self, users, instruments):
        today = timezone.now().date()
        admin = users["admin"]
        insp_rajesh = users["inspector_rajesh"]
        insp_anita = users["inspector_anita"]

        # Mapping of all 25 instruments to workflow states and certificates:
        # Statuses covered: SUBMITTED (3), ASSIGNED (3), FAILED (2), CANCELLED (2), CERTIFIED (15)
        # Certificate states: VALID (8), EXPIRING within 30d (4: 30d, 7d, 15d, 25d), EXPIRED (2), REVOKED (1)
        configs = [
            # Owner 1 (Ramesh)
            {
                "serial": "LK-CS-001",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=180),
                "issued_on": today - datetime.timedelta(days=185),
                "inspector": insp_rajesh,
                "cert_seq": 101,
            },
            {
                "serial": "LK-CS-002",
                "workflow": "CERTIFIED",
                "cert_state": "EXPIRING_30",  # EXACTLY 30 DAYS REMAINING
                "valid_until": today + datetime.timedelta(days=30),
                "issued_on": today - datetime.timedelta(days=335),
                "inspector": insp_rajesh,
                "cert_seq": 102,
            },
            {
                "serial": "LK-PS-003",
                "workflow": "CERTIFIED",
                "cert_state": "EXPIRING_7",   # EXACTLY 7 DAYS REMAINING
                "valid_until": today + datetime.timedelta(days=7),
                "issued_on": today - datetime.timedelta(days=358),
                "inspector": insp_rajesh,
                "cert_seq": 103,
            },
            {
                "serial": "LK-CS-004",
                "workflow": "SUBMITTED",
                "inspector": None,
            },
            {
                "serial": "LK-PS-005",
                "workflow": "ASSIGNED",
                "inspector": insp_rajesh,
            },

            # Owner 2 (Priya)
            {
                "serial": "SJ-GB-001",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=240),
                "issued_on": today - datetime.timedelta(days=125),
                "inspector": insp_anita,
                "cert_seq": 104,
            },
            {
                "serial": "SJ-GB-002",
                "workflow": "CERTIFIED",
                "cert_state": "EXPIRING_15",  # 15 days remaining (non-reminder threshold)
                "valid_until": today + datetime.timedelta(days=15),
                "issued_on": today - datetime.timedelta(days=350),
                "inspector": insp_anita,
                "cert_seq": 105,
            },
            {
                "serial": "SJ-CS-003",
                "workflow": "CERTIFIED",
                "cert_state": "EXPIRED",      # Expired in past
                "valid_until": today - datetime.timedelta(days=20),
                "issued_on": today - datetime.timedelta(days=385),
                "inspector": insp_anita,
                "cert_seq": 106,
            },
            {
                "serial": "SJ-CS-004",
                "workflow": "SUBMITTED",
                "inspector": None,
            },
            {
                "serial": "SJ-CS-005",
                "workflow": "ASSIGNED",
                "inspector": insp_anita,
            },

            # Owner 3 (Manpreet)
            {
                "serial": "PHW-WB-001",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=300),
                "issued_on": today - datetime.timedelta(days=65),
                "inspector": insp_rajesh,
                "cert_seq": 107,
            },
            {
                "serial": "PHW-WB-002",
                "workflow": "CERTIFIED",
                "cert_state": "REVOKED",     # Revoked by admin
                "valid_until": today + datetime.timedelta(days=200),
                "issued_on": today - datetime.timedelta(days=165),
                "revoked_at": timezone.now() - datetime.timedelta(days=5),
                "revoked_by": admin,
                "revoked_reason": "Security seal broken and unauthorized software bypass detected during surprise vigilance audit.",
                "inspector": insp_rajesh,
                "cert_seq": 108,
            },
            {
                "serial": "PHW-PS-003",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=90),
                "issued_on": today - datetime.timedelta(days=275),
                "inspector": insp_rajesh,
                "cert_seq": 109,
            },
            {
                "serial": "PHW-PS-004",
                "workflow": "FAILED",
                "inspector": insp_rajesh,
                "failure_reason": "Eccentricity test exceeded maximum permissible error limit of 1.5e.",
            },
            {
                "serial": "PHW-WB-005",
                "workflow": "CANCELLED",
                "inspector": None,
                "cancel_reason": "Owner requested postponement due to highway resurfacing works.",
            },

            # Owner 4 (Fatima)
            {
                "serial": "DOT-CM-001",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=120),
                "issued_on": today - datetime.timedelta(days=245),
                "inspector": insp_anita,
                "cert_seq": 110,
            },
            {
                "serial": "DOT-CM-002",
                "workflow": "CERTIFIED",
                "cert_state": "EXPIRING_25",  # 25 days remaining
                "valid_until": today + datetime.timedelta(days=25),
                "issued_on": today - datetime.timedelta(days=340),
                "inspector": insp_anita,
                "cert_seq": 111,
            },
            {
                "serial": "DOT-PS-003",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=320),
                "issued_on": today - datetime.timedelta(days=45),
                "inspector": insp_anita,
                "cert_seq": 112,
            },
            {
                "serial": "DOT-CS-004",
                "workflow": "FAILED",
                "inspector": insp_anita,
                "failure_reason": "Zero return check failed; unstable resting display indication.",
            },
            {
                "serial": "DOT-CM-005",
                "workflow": "CANCELLED",
                "inspector": None,
                "cancel_reason": "Measure scheduled for replacement with new SS-304 volumetric cylinder.",
            },

            # Owner 5 (Vikram)
            {
                "serial": "DAG-PS-001",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=270),
                "issued_on": today - datetime.timedelta(days=95),
                "inspector": insp_rajesh,
                "cert_seq": 113,
            },
            {
                "serial": "DAG-PS-002",
                "workflow": "CERTIFIED",
                "cert_state": "EXPIRED",      # Expired in past
                "valid_until": today - datetime.timedelta(days=45),
                "issued_on": today - datetime.timedelta(days=410),
                "inspector": insp_rajesh,
                "cert_seq": 114,
            },
            {
                "serial": "DAG-LM-003",
                "workflow": "CERTIFIED",
                "cert_state": "VALID",
                "valid_until": today + datetime.timedelta(days=150),
                "issued_on": today - datetime.timedelta(days=215),
                "inspector": insp_anita,
                "cert_seq": 115,
            },
            {
                "serial": "DAG-CS-004",
                "workflow": "SUBMITTED",
                "inspector": None,
            },
            {
                "serial": "DAG-CS-005",
                "workflow": "ASSIGNED",
                "inspector": insp_rajesh,
            },
        ]

        for item in configs:
            inst = instruments[item["serial"]]
            owner = inst.business.owner
            workflow = item["workflow"]
            inspector = item["inspector"]

            # Look up or create request
            req = VerificationRequest.objects.filter(instrument=inst).first()
            if not req:
                req = VerificationRequest.objects.create(
                    instrument=inst,
                    requested_by=owner,
                    preferred_date=today + datetime.timedelta(days=7),
                    status=RequestStatus.SUBMITTED,
                    notes=f"Statutory verification for {inst.serial_no}",
                )

            # Apply workflow state
            if workflow == "SUBMITTED":
                req.status = RequestStatus.SUBMITTED
                req.inspector = None
                req.save()
                StatusEvent.objects.get_or_create(
                    request=req,
                    to_status=RequestStatus.SUBMITTED,
                    defaults={"actor": owner, "note": "Initial verification request submitted."},
                )

            elif workflow == "ASSIGNED":
                req.status = RequestStatus.ASSIGNED
                req.inspector = inspector
                req.save()
                StatusEvent.objects.get_or_create(
                    request=req,
                    to_status=RequestStatus.ASSIGNED,
                    defaults={"actor": admin, "note": f"Assigned to Inspector {inspector.get_full_name()}."},
                )

            elif workflow == "CANCELLED":
                req.status = RequestStatus.CANCELLED
                req.inspector = None
                req.save()
                StatusEvent.objects.get_or_create(
                    request=req,
                    to_status=RequestStatus.CANCELLED,
                    defaults={"actor": owner, "note": item.get("cancel_reason", "Request cancelled by owner.")},
                )

            elif workflow == "FAILED":
                req.status = RequestStatus.FAILED
                req.inspector = inspector
                req.save()
                insp, _ = Inspection.objects.get_or_create(
                    request=req,
                    defaults={
                        "inspector": inspector,
                        "zero_ok": False if "Zero" in item.get("failure_reason", "") else True,
                        "result": InspectionResult.FAIL,
                        "remarks": item.get("failure_reason", "Instrument exceeded maximum permissible error limits."),
                    },
                )
                insp.result = InspectionResult.FAIL
                insp.remarks = item.get("failure_reason", "Instrument exceeded maximum permissible error limits.")
                insp.save()
                # Create fail reading
                TestReading.objects.filter(inspection=insp).delete()
                TestReading.objects.create(
                    inspection=insp,
                    kind=ReadingKind.ACCURACY,
                    test_load=Decimal("10.0000"),
                    indication=Decimal("10.0800"),  # Significant error
                    error=Decimal("0.0800"),
                    mpe=Decimal("0.0100"),
                    within_limit=False,
                )
                StatusEvent.objects.get_or_create(
                    request=req,
                    to_status=RequestStatus.FAILED,
                    defaults={"actor": inspector, "note": f"Inspection failed: {insp.remarks}"},
                )

            elif workflow == "CERTIFIED":
                req.status = RequestStatus.CERTIFIED
                req.inspector = inspector
                req.save()
                insp, _ = Inspection.objects.get_or_create(
                    request=req,
                    defaults={
                        "inspector": inspector,
                        "zero_ok": True,
                        "result": InspectionResult.PASS,
                        "remarks": "Instrument thoroughly verified against working standards. Calibration within legal tolerance.",
                    },
                )
                insp.result = InspectionResult.PASS
                insp.zero_ok = True
                insp.save()

                # Passing readings
                TestReading.objects.filter(inspection=insp).delete()
                TestReading.objects.create(
                    inspection=insp,
                    kind=ReadingKind.ACCURACY,
                    test_load=Decimal("5.0000"),
                    indication=Decimal("5.0010"),
                    error=Decimal("0.0010"),
                    mpe=Decimal("0.0050"),
                    within_limit=True,
                )
                TestReading.objects.create(
                    inspection=insp,
                    kind=ReadingKind.REPEATABILITY,
                    test_load=Decimal("10.0000"),
                    indication=Decimal("10.0000"),
                    error=Decimal("0.0000"),
                    mpe=Decimal("0.0100"),
                    within_limit=True,
                )

                cert_seq = item.get("cert_seq", 100)
                cert_number = f"TOLA-2026-{cert_seq:06d}"
                cert = Certificate.objects.filter(inspection=insp).first()
                if not cert:
                    cert = Certificate.objects.create(
                        inspection=insp,
                        number=cert_number,
                        issued_on=item["issued_on"],
                        valid_until=item["valid_until"],
                    )
                else:
                    cert.number = cert_number
                    cert.issued_on = item["issued_on"]
                    cert.valid_until = item["valid_until"]

                # Revocation handling
                if item.get("cert_state") == "REVOKED":
                    cert.revoked_at = item.get("revoked_at")
                    cert.revoked_by = item.get("revoked_by")
                    cert.revoked_reason = item.get("revoked_reason")
                else:
                    cert.revoked_at = None
                    cert.revoked_by = None
                    cert.revoked_reason = ""
                cert.save()

                StatusEvent.objects.get_or_create(
                    request=req,
                    to_status=RequestStatus.CERTIFIED,
                    defaults={"actor": inspector, "note": f"Verification certificate #{cert.number} issued."},
                )

    def _print_credentials(self, users):
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Tola Demo Credentials & Role Directory ---"))
        self.stdout.write(
            f"{'Role':<12} | {'Username':<18} | {'Password':<22} | {'Full Name':<20} | {'Phone':<16}"
        )
        self.stdout.write("-" * 96)

        user_rows = [
            (users["admin"], "AdminPassword123!"),
            (users["inspector_rajesh"], "InspectorPassword123!"),
            (users["inspector_anita"], "InspectorPassword123!"),
            (users["owner_ramesh"], "OwnerPassword123!"),
            (users["owner_priya"], "OwnerPassword123!"),
            (users["owner_manpreet"], "OwnerPassword123!"),
            (users["owner_fatima"], "OwnerPassword123!"),
            (users["owner_vikram"], "OwnerPassword123!"),
        ]

        for u, pwd in user_rows:
            self.stdout.write(
                f"{u.get_role_display():<12} | {u.username:<18} | {pwd:<22} | "
                f"{u.get_full_name():<20} | {u.phone or 'N/A':<16}"
            )

        self.stdout.write("-" * 96)

        self.stdout.write("\nSummary of Seeded Data Ledger:")
        self.stdout.write(f"  Total Registered Businesses: {Business.objects.count()}")
        self.stdout.write(f"  Total Instruments:          {Instrument.objects.count()}")
        self.stdout.write(f"  Total Verification Requests:{VerificationRequest.objects.count()}")
        self.stdout.write(
            f"    - SUBMITTED:  {VerificationRequest.objects.filter(status=RequestStatus.SUBMITTED).count()}"
        )
        self.stdout.write(
            f"    - ASSIGNED:   {VerificationRequest.objects.filter(status=RequestStatus.ASSIGNED).count()}"
        )
        self.stdout.write(
            f"    - CERTIFIED:  {VerificationRequest.objects.filter(status=RequestStatus.CERTIFIED).count()}"
        )
        self.stdout.write(
            f"    - FAILED:     {VerificationRequest.objects.filter(status=RequestStatus.FAILED).count()}"
        )
        self.stdout.write(
            f"    - CANCELLED:  {VerificationRequest.objects.filter(status=RequestStatus.CANCELLED).count()}"
        )

        today = timezone.now().date()
        certs = Certificate.objects.all()
        valid_count = sum(1 for c in certs if c.state == "VALID" and (c.valid_until - today).days > 30)
        expiring_count = sum(1 for c in certs if c.state == "VALID" and 0 <= (c.valid_until - today).days <= 30)
        expired_count = sum(1 for c in certs if c.state == "EXPIRED")
        revoked_count = sum(1 for c in certs if c.state == "REVOKED")

        self.stdout.write(f"  Total Certificates:         {certs.count()}")
        self.stdout.write(f"    - VALID (>30 days):         {valid_count}")
        self.stdout.write(f"    - EXPIRING (within 30 days):{expiring_count}")
        self.stdout.write(f"    - EXPIRED:                  {expired_count}")
        self.stdout.write(f"    - REVOKED:                  {revoked_count}")
        self.stdout.write("")
