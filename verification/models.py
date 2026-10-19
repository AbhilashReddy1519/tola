from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class RequestStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    ASSIGNED = "ASSIGNED", "Assigned"
    PASSED = "PASSED", "Passed"
    FAILED = "FAILED", "Failed"
    CERTIFIED = "CERTIFIED", "Certified"
    CANCELLED = "CANCELLED", "Cancelled"


class InspectionResult(models.TextChoices):
    PASS = "PASS", "Pass"
    FAIL = "FAIL", "Fail"


class ReadingKind(models.TextChoices):
    ACCURACY = "ACCURACY", "Accuracy"
    REPEATABILITY = "REPEATABILITY", "Repeatability"
    ECCENTRICITY = "ECCENTRICITY", "Eccentricity"


class VerificationRequest(models.Model):
    instrument = models.ForeignKey(
        "registry.Instrument",
        on_delete=models.CASCADE,
        related_name="verification_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_verifications",
    )
    preferred_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.SUBMITTED,
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_inspections",
        limit_choices_to={"role": "INSPECTOR"},
    )
    fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal(str(getattr(settings, "VERIFICATION_FEE", 500))),
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"VR-{self.pk}: {self.instrument} ({self.get_status_display()})"


class Inspection(models.Model):
    request = models.OneToOneField(
        VerificationRequest,
        on_delete=models.CASCADE,
        related_name="inspection",
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inspections",
    )
    inspected_at = models.DateTimeField(default=timezone.now)
    zero_ok = models.BooleanField(default=True)
    remarks = models.TextField(blank=True)
    result = models.CharField(
        max_length=10,
        choices=InspectionResult.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inspected_at"]

    def __str__(self):
        return f"Inspection for VR-{self.request_id} ({self.result})"


class TestReading(models.Model):
    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        related_name="readings",
    )
    kind = models.CharField(
        max_length=20,
        choices=ReadingKind.choices,
        default=ReadingKind.ACCURACY,
    )
    test_load = models.DecimalField(max_digits=12, decimal_places=4)
    indication = models.DecimalField(max_digits=12, decimal_places=4)
    error = models.DecimalField(max_digits=12, decimal_places=4)
    mpe = models.DecimalField(max_digits=12, decimal_places=4)
    within_limit = models.BooleanField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        status = "OK" if self.within_limit else "EXCEEDED"
        return f"{self.get_kind_display()} reading: Load={self.test_load}, Ind={self.indication}, Error={self.error} [{status}]"


class StatusEvent(models.Model):
    request = models.ForeignKey(
        VerificationRequest,
        on_delete=models.CASCADE,
        related_name="events",
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["at"]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"VR-{self.request_id}: {self.from_status or 'START'} -> {self.to_status} by {actor_name} at {self.at}"
