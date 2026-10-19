from django.urls import path
from . import views

urlpatterns = [
    # PDF download
    path("app/certificates/<str:number>/pdf/", views.CertificatePDFDownloadView.as_view(), name="certificate_pdf"),

    # Admin Revoke
    path("app/console/certificates/<str:number>/revoke/", views.AdminRevokeCertificateView.as_view(), name="certificate_revoke"),

    # Public Verification endpoints
    path("v/<uuid:token>/", views.PublicTokenVerifyView.as_view(), name="public_token_verify"),
    path("verify/", views.PublicManualVerifyView.as_view(), name="public_manual_verify"),
]
