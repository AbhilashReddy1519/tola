from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone
from registry.models import Instrument
from certificates.models import Certificate


def landing(request):
    instruments_verified = (
        Instrument.objects.filter(verification_requests__inspection__certificate__isnull=False)
        .distinct()
        .count()
    )
    certificates_active = Certificate.objects.filter(
        revoked_at__isnull=True,
        valid_until__gte=timezone.now().date(),
    ).count()

    certs = Certificate.objects.select_related("inspection__request").all()
    durations = []
    for cert in certs:
        try:
            req = cert.inspection.request
            if req and req.created_at:
                diff = (cert.issued_on - req.created_at.date()).days
                durations.append(max(diff, 1))
        except Exception:
            pass

    avg_days = round(sum(durations) / len(durations), 1) if durations else 1.2

    context = {
        "instruments_verified": instruments_verified,
        "certificates_active": certificates_active,
        "avg_days_to_certify": avg_days,
    }
    return render(request, "site_pages/landing.html", context)


def styleguide(request):
    if not settings.DEBUG:
        raise Http404("Styleguide is only available in DEBUG mode.")
    return render(request, "site_pages/styleguide.html")
