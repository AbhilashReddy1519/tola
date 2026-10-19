from django.db import transaction

from .models import RequestStatus, StatusEvent

ALLOWED_TRANSITIONS = {
    RequestStatus.SUBMITTED: [
        RequestStatus.ASSIGNED,
        RequestStatus.CANCELLED,
    ],
    RequestStatus.ASSIGNED: [
        RequestStatus.PASSED,
        RequestStatus.FAILED,
        RequestStatus.CANCELLED,
    ],
    RequestStatus.PASSED: [
        RequestStatus.CERTIFIED,
    ],
    RequestStatus.FAILED: [],
    RequestStatus.CERTIFIED: [],
    RequestStatus.CANCELLED: [],
}


class InvalidTransitionError(Exception):
    """Raised when an illegal status change is attempted."""
    pass


def transition(request, to_status, actor=None, note=""):
    """
    Execute a verified state machine transition for a VerificationRequest.
    Validates against ALLOWED_TRANSITIONS, wraps in transaction.atomic,
    updates request status, and records an immutable StatusEvent audit log entry.
    """
    from_status = request.status

    # Normalize to string/enum value if passed as enum
    if hasattr(to_status, "value"):
        to_status = to_status.value

    allowed = [
        s.value if hasattr(s, "value") else str(s)
        for s in ALLOWED_TRANSITIONS.get(from_status, [])
    ]

    if to_status not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition verification request #{request.pk} from '{from_status}' to '{to_status}'."
        )

    with transaction.atomic():
        request.status = to_status
        request.save(update_fields=["status", "updated_at"])
        event = StatusEvent.objects.create(
            request=request,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            note=note or "",
        )

    return event
