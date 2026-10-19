import uuid
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from accounts.mixins import RoleRequiredMixin
from .models import Certificate
from .pdf import generate_certificate_pdf
from .services import revoke_certificate

User = get_user_model()


class CertificatePDFDownloadView(View):
    """
    Download the official certificate PDF.
    Owner of the instrument or admin may download the PDF. Everyone else gets 404.
    """
    def get(self, request, number):
        cert = get_object_or_404(
            Certificate.objects.select_related(
                "inspection__request__instrument__business__owner",
                "inspection__inspector",
            ),
            number=number,
        )

        user = request.user
        if not user.is_authenticated:
            raise Http404("Certificate not found.")

        is_owner = cert.inspection.request.instrument.business.owner == user
        is_admin = getattr(user, "role", None) == User.Role.ADMIN or user.is_staff

        if not (is_owner or is_admin):
            raise Http404("Certificate not found.")

        pdf_bytes = generate_certificate_pdf(cert)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{cert.number}.pdf"'
        return response


class PublicTokenVerifyView(View):
    """
    Public verification page (/v/<token>/) reached via QR code scan or link.
    Displays the state word (VALID, EXPIRED, REVOKED) at display size.
    Does not leak owner email or phone number.
    """
    def get(self, request, token):
        try:
            token_uuid = uuid.UUID(str(token))
        except (ValueError, TypeError):
            raise Http404("Invalid certificate token format.")

        cert = get_object_or_404(
            Certificate.objects.select_related(
                "inspection__request__instrument__business",
                "inspection__inspector",
            ),
            token=token_uuid,
        )

        instrument = cert.inspection.request.instrument
        business = instrument.business

        can_download = False
        if request.user.is_authenticated:
            if business.owner == request.user or getattr(request.user, "role", None) == User.Role.ADMIN:
                can_download = True

        return render(request, "certificates/public_verify.html", {
            "cert": cert,
            "instrument": instrument,
            "business": business,
            "can_download": can_download,
        })


class PublicManualVerifyView(View):
    """
    Public manual number lookup (/verify/).
    Enables users to enter a certificate number (e.g. TOLA-2026-000001) to verify validity.
    """
    def get(self, request):
        query = request.GET.get("number", "").strip()
        cert = None
        searched = bool(query)

        if query:
            cert = Certificate.objects.filter(number__iexact=query).select_related(
                "inspection__request__instrument__business",
                "inspection__inspector",
            ).first()

        return render(request, "certificates/manual_verify.html", {
            "query": query,
            "cert": cert,
            "searched": searched,
        })


class AdminRevokeCertificateView(RoleRequiredMixin, View):
    """
    Admin revoke view (/app/console/certificates/<number>/revoke/).
    Requires ADMIN role. Prompts for reason and transitions certificate to REVOKED.
    """
    allowed_roles = [User.Role.ADMIN]

    def get(self, request, number):
        cert = get_object_or_404(
            Certificate.objects.select_related("inspection__request__instrument__business"),
            number=number,
        )
        return render(request, "certificates/admin_revoke.html", {"cert": cert})

    def post(self, request, number):
        cert = get_object_or_404(
            Certificate.objects.select_related("inspection__request__instrument__business"),
            number=number,
        )
        reason = request.POST.get("reason", "").strip()
        if not reason:
            messages.error(request, "A revocation reason is required by legal metrology compliance rules.")
            return render(request, "certificates/admin_revoke.html", {"cert": cert})

        revoke_certificate(cert, reason=reason, actor=request.user)
        messages.warning(request, f"Certificate #{cert.number} has been officially REVOKED.")
        return redirect("public_token_verify", token=cert.token)
