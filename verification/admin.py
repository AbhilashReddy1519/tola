from django.contrib import admin
from .models import Inspection, StatusEvent, TestReading, VerificationRequest


class TestReadingInline(admin.TabularInline):
    model = TestReading
    extra = 0
    readonly_fields = ("kind", "test_load", "indication", "error", "mpe", "within_limit")


class StatusEventInline(admin.TabularInline):
    model = StatusEvent
    extra = 0
    readonly_fields = ("from_status", "to_status", "actor", "at", "note")


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "instrument",
        "requested_by",
        "preferred_date",
        "status",
        "inspector",
        "created_at",
    )
    list_filter = ("status", "preferred_date")
    search_fields = ("instrument__serial_no", "requested_by__username", "inspector__username")
    raw_id_fields = ("instrument", "requested_by", "inspector")
    inlines = [StatusEventInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "instrument", "instrument__business", "requested_by", "inspector"
        )


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "inspector",
        "zero_ok",
        "result",
        "inspected_at",
    )
    list_filter = ("result", "zero_ok")
    raw_id_fields = ("request", "inspector")
    inlines = [TestReadingInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "request", "inspector", "request__instrument"
        )


@admin.register(TestReading)
class TestReadingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "inspection",
        "kind",
        "test_load",
        "indication",
        "error",
        "mpe",
        "within_limit",
    )
    list_filter = ("kind", "within_limit")
    raw_id_fields = ("inspection",)


@admin.register(StatusEvent)
class StatusEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "request",
        "from_status",
        "to_status",
        "actor",
        "at",
    )
    list_filter = ("to_status", "from_status")
    raw_id_fields = ("request", "actor")
