import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def default_uuid():
    return uuid.uuid4()


class Certificate(models.Model):
    inspection = models.OneToOneField(
        "verification.Inspection",
        on_delete=models.CASCADE,
        related_name="certificate",
    )
    number = models.CharField(max_length=50, unique=True, db_index=True)
    token = models.UUIDField(default=default_uuid, unique=True, editable=False, db_index=True)
    issued_on = models.DateField(default=timezone.now)
    valid_until = models.DateField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.TextField(blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="revoked_certificates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issued_on", "-created_at"]

    def __str__(self):
        return f"Certificate {self.number} ({self.state})"

    @property
    def state(self):
        """Derived state: VALID, EXPIRED, or REVOKED."""
        if self.revoked_at is not None:
            return "REVOKED"
        if self.valid_until and self.valid_until < timezone.now().date():
            return "EXPIRED"
        return "VALID"

    @property
    def is_valid(self):
        return self.state == "VALID"
