from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "get_instrument",
        "get_business",
        "issued_on",
        "valid_until",
        "state",
        "token",
    )
    list_filter = ("issued_on", "valid_until")
    search_fields = (
        "number",
        "token",
        "inspection__request__instrument__serial_no",
        "inspection__request__instrument__business__name",
    )
    raw_id_fields = ("inspection", "revoked_by")
    readonly_fields = ("token", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "inspection__request__instrument__business",
            "inspection__inspector",
            "revoked_by",
        )

    @admin.display(description="Instrument")
    def get_instrument(self, obj):
        inst = obj.inspection.request.instrument
        return f"{inst.make} {inst.model_no} ({inst.serial_no})"

    @admin.display(description="Business")
    def get_business(self, obj):
        return obj.inspection.request.instrument.business.name
