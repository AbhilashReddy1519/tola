import calendar
import uuid
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from verification.models import InspectionResult, RequestStatus
from verification.services import transition
from .models import Certificate


def generate_certificate_number(year=None):
    """
    Generate sequential certificate number in format: TOLA-<year>-<6 digit sequence>
    Uses select_for_update() inside a transaction to prevent race conditions.
    """
    if year is None:
        year = timezone.now().year

    prefix = f"TOLA-{year}-"
    last_cert = (
        Certificate.objects.filter(number__startswith=prefix)
        .order_by("-number")
        .select_for_update()
        .first()
    )

    if last_cert:
        try:
            last_seq = int(last_cert.number.split("-")[-1])
            seq = last_seq + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:06d}"


@db_transaction.atomic
def issue_certificate(inspection, actor=None):
    """
    Issue a Certificate for a passed inspection.
    Executes in the same transaction as transitioning the request to CERTIFIED.
    Raises ValueError if inspection did not pass.
    """
    if inspection.result != InspectionResult.PASS:
        raise ValueError("Cannot issue a certificate for an inspection that did not PASS.")

    if hasattr(inspection, "certificate"):
        return inspection.certificate

    today = timezone.now().date()
    validity_months = getattr(settings, "CERT_VALIDITY_MONTHS", 12)

    # Calculate exact validity date (e.g. 12 months forward)
    month = today.month - 1 + validity_months
    year = today.year + month // 12
    month = month % 12 + 1
    day = min(today.day, calendar.monthrange(year, month)[1])
    valid_until = today.replace(year=year, month=month, day=day)

    number = generate_certificate_number(today.year)
    token = uuid.uuid4()

    cert = Certificate.objects.create(
        inspection=inspection,
        number=number,
        token=token,
        issued_on=today,
        valid_until=valid_until,
    )

    # Transition the request to CERTIFIED in the same transaction
    transition(
        inspection.request,
        RequestStatus.CERTIFIED,
        actor=actor,
        note=f"Official Verification Certificate #{number} issued.",
    )

    return cert


@db_transaction.atomic
def revoke_certificate(certificate, reason, actor=None):
    """
    Revoke an active Certificate with an audit reason and timestamp.
    """
    certificate.revoked_at = timezone.now()
    certificate.revoked_reason = reason.strip()
    certificate.revoked_by = actor
    certificate.save(update_fields=["revoked_at", "revoked_reason", "revoked_by", "updated_at"])
    return certificate
