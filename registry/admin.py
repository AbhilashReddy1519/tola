from django.contrib import admin
from .models import Business, Instrument


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "trade_type",
        "district",
        "pincode",
        "licence_no",
        "created_at",
    )
    list_filter = ("trade_type", "district")
    search_fields = ("name", "owner__username", "district", "licence_no")
    raw_id_fields = ("owner",)


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = (
        "serial_no",
        "business",
        "category",
        "make",
        "model_no",
        "max_capacity",
        "unit",
        "accuracy_class",
        "created_at",
    )
    list_filter = ("category", "accuracy_class", "unit")
    search_fields = ("serial_no", "make", "model_no", "business__name")
    raw_id_fields = ("business",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("business", "business__owner")
