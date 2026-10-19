from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class TradeType(models.TextChoices):
    GROCERY = "grocery", "Grocery"
    JEWELLERY = "jewellery", "Jewellery"
    FUEL = "fuel", "Fuel"
    WEIGHBRIDGE = "weighbridge", "Weighbridge"
    OTHER = "other", "Other"


class Category(models.TextChoices):
    COUNTER_SCALE = "counter_scale", "Counter scale"
    PLATFORM_SCALE = "platform_scale", "Platform scale"
    WEIGHBRIDGE = "weighbridge", "Weighbridge"
    LENGTH_MEASURE = "length_measure", "Length measure"
    CAPACITY_MEASURE = "capacity_measure", "Capacity measure"


class Unit(models.TextChoices):
    G = "g", "g"
    KG = "kg", "kg"
    T = "t", "t"
    M = "m", "m"
    L = "L", "L"


class AccuracyClass(models.TextChoices):
    CLASS_I = "I", "Class I"
    CLASS_II = "II", "Class II"
    CLASS_III = "III", "Class III"
    CLASS_IIII = "IIII", "Class IIII"


class Business(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="businesses",
        limit_choices_to={"role": "OWNER"},
    )
    name = models.CharField(max_length=255)
    trade_type = models.CharField(max_length=50, choices=TradeType.choices)
    address = models.TextField()
    district = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    licence_no = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Businesses"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Instrument(models.Model):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="instruments",
    )
    category = models.CharField(max_length=50, choices=Category.choices)
    make = models.CharField(max_length=100)
    model_no = models.CharField(max_length=100)
    serial_no = models.CharField(max_length=100)
    max_capacity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    unit = models.CharField(max_length=10, choices=Unit.choices)
    scale_interval_e = models.DecimalField(max_digits=10, decimal_places=4)
    accuracy_class = models.CharField(
        max_length=10,
        choices=AccuracyClass.choices,
        default=AccuracyClass.CLASS_III,
    )
    installed_on = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "serial_no"],
                name="unique_business_instrument_serial",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} ({self.make} {self.model_no} - {self.serial_no})"

    def clean(self):
        super().clean()
        if self.max_capacity is not None and self.max_capacity <= Decimal("0"):
            raise ValidationError(
                {"max_capacity": "Maximum capacity must be strictly greater than 0."}
            )

    @property
    def current_certificate(self):
        """Returns the latest certificate issued for this instrument."""
        from certificates.models import Certificate
        return (
            Certificate.objects.filter(inspection__request__instrument=self)
            .order_by("-issued_on", "-created_at")
            .first()
        )

    @property
    def status(self):
        """Derived status: Unverified, Pending, Valid, Expiring soon, Expired, Failed, Revoked."""
        latest_req = self.verification_requests.order_by("-created_at").first()
        if latest_req and latest_req.status in ["SUBMITTED", "ASSIGNED"]:
            return "Pending"

        cert = self.current_certificate
        if cert is None:
            if latest_req and latest_req.status == "FAILED":
                return "Failed"
            return "Unverified"

        if cert.revoked_at is not None:
            return "Revoked"

        from django.utils import timezone
        today = timezone.now().date()
        if cert.valid_until < today:
            return "Expired"

        days_left = (cert.valid_until - today).days
        if days_left <= 30:
            return "Expiring soon"

        return "Valid"

    @property
    def days_to_expiry(self):
        cert = self.current_certificate
        if cert and cert.valid_until:
            from django.utils import timezone
            return (cert.valid_until - timezone.now().date()).days
        return None
