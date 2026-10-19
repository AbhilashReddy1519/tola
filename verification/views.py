from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction as db_transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from registry.models import Instrument
from .forms import AssignInspectorForm, InspectionSubmitForm, VerificationRequestForm
from .models import Inspection, InspectionResult, ReadingKind, RequestStatus, StatusEvent, TestReading, VerificationRequest
from .rules import evaluate_reading, is_inspection_passing
from .services import InvalidTransitionError, transition

User = get_user_model()


# ---------------------------------------------------------------------------
# OWNER VIEWS
# ---------------------------------------------------------------------------

class OwnerRequestListView(RoleRequiredMixin, ListView):
    allowed_roles = [User.Role.OWNER]
    model = VerificationRequest
    template_name = "verification/owner_request_list.html"
    context_object_name = "requests"

    def get_queryset(self):
        return (
            VerificationRequest.objects.filter(requested_by=self.request.user)
            .select_related("instrument", "instrument__business", "inspector")
            .order_by("-created_at")
        )


class OwnerRequestCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.Role.OWNER]
    model = VerificationRequest
    form_class = VerificationRequestForm
    template_name = "verification/owner_request_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        instrument_pk = self.request.GET.get("instrument")
        if instrument_pk:
            # Validate that instrument belongs to the requesting user
            get_object_or_404(
                Instrument.objects.filter(business__owner=self.request.user),
                pk=instrument_pk,
            )
            initial["instrument"] = instrument_pk
        return initial

    def form_valid(self, form):
        # Enforce that selected instrument is owned by the user
        instrument = form.cleaned_data["instrument"]
        if instrument.business.owner != self.request.user:
            raise PermissionDenied("You cannot request verification for an instrument you do not own.")

        with db_transaction.atomic():
            form.instance.requested_by = self.request.user
            form.instance.status = RequestStatus.SUBMITTED
            self.object = form.save()
            StatusEvent.objects.create(
                request=self.object,
                from_status="",
                to_status=RequestStatus.SUBMITTED,
                actor=self.request.user,
                note=form.cleaned_data.get("notes") or "Initial verification request submitted.",
            )

        messages.success(self.request, f"Verification request #{self.object.pk} submitted successfully.")
        return redirect("owner_request_detail", pk=self.object.pk)


class OwnerRequestDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [User.Role.OWNER]
    model = VerificationRequest
    template_name = "verification/owner_request_detail.html"
    context_object_name = "req"

    def get_queryset(self):
        return (
            VerificationRequest.objects.filter(requested_by=self.request.user)
            .select_related("instrument", "instrument__business", "inspector")
            .prefetch_related("events__actor", "inspection__readings")
        )


class OwnerRequestCancelView(RoleRequiredMixin, View):
    allowed_roles = [User.Role.OWNER]

    def post(self, request, pk):
        req = get_object_or_404(
            VerificationRequest.objects.filter(requested_by=request.user),
            pk=pk,
        )
        try:
            transition(
                req,
                RequestStatus.CANCELLED,
                actor=request.user,
                note="Cancelled by business owner.",
            )
            messages.info(request, f"Verification request #{req.pk} has been cancelled.")
        except InvalidTransitionError as e:
            messages.error(request, str(e))

        return redirect("owner_request_detail", pk=req.pk)


# ---------------------------------------------------------------------------
# ADMIN CONSOLE VIEWS
# ---------------------------------------------------------------------------

class AdminConsoleRequestListView(RoleRequiredMixin, ListView):
    allowed_roles = [User.Role.ADMIN]
    model = VerificationRequest
    template_name = "verification/admin_request_list.html"
    context_object_name = "requests"

    def get_queryset(self):
        return (
            VerificationRequest.objects.all()
            .select_related("instrument", "instrument__business", "inspector", "requested_by")
            .order_by("-created_at")
        )


class AdminAssignInspectorView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.Role.ADMIN]
    model = VerificationRequest
    form_class = AssignInspectorForm
    template_name = "verification/admin_assign_form.html"
    context_object_name = "req"

    def form_valid(self, form):
        req = self.get_object()
        inspector = form.cleaned_data["inspector"]
        note = form.cleaned_data.get("notes") or f"Assigned to Inspector {inspector.get_full_name() or inspector.username}."

        if inspector.role != User.Role.INSPECTOR:
            raise PermissionDenied("Only users with the INSPECTOR role may be assigned.")

        with db_transaction.atomic():
            req.inspector = inspector
            req.save(update_fields=["inspector"])
            transition(req, RequestStatus.ASSIGNED, actor=self.request.user, note=note)

        messages.success(self.request, f"Request #{req.pk} assigned to {inspector.username}.")
        return redirect("admin_request_list")


# ---------------------------------------------------------------------------
# INSPECTOR VIEWS
# ---------------------------------------------------------------------------

class InspectorQueueView(RoleRequiredMixin, ListView):
    allowed_roles = [User.Role.INSPECTOR]
    model = VerificationRequest
    template_name = "verification/inspector_queue.html"
    context_object_name = "requests"

    def get_queryset(self):
        return (
            VerificationRequest.objects.filter(
                inspector=self.request.user,
                status=RequestStatus.ASSIGNED,
            )
            .select_related("instrument", "instrument__business", "requested_by")
            .order_by("preferred_date", "created_at")
        )


class InspectorInspectionView(RoleRequiredMixin, View):
    allowed_roles = [User.Role.INSPECTOR]
    template_name = "verification/inspector_inspect.html"

    def get_object(self, pk):
        # Strictly return 404 if request is not assigned to the logged-in inspector
        return get_object_or_404(
            VerificationRequest.objects.filter(
                inspector=self.request.user,
                status=RequestStatus.ASSIGNED,
            ).select_related("instrument", "instrument__business"),
            pk=pk,
        )

    def get(self, request, pk):
        req = self.get_object(pk)
        return render(request, self.template_name, {
            "req": req,
            "instrument": req.instrument,
            "kinds": ReadingKind.choices,
        })

    def post(self, request, pk):
        req = self.get_object(pk)
        instrument = req.instrument

        zero_ok = request.POST.get("zero_ok") == "true" or request.POST.get("zero_ok") == "on"
        remarks = request.POST.get("remarks", "").strip()

        # Extract submitted test readings from POST
        kinds = request.POST.getlist("kind[]")
        loads = request.POST.getlist("test_load[]")
        indications = request.POST.getlist("indication[]")

        evaluated_readings = []
        for kind, load_str, ind_str in zip(kinds, loads, indications):
            try:
                load = Decimal(load_str)
                indication = Decimal(ind_str)
                evaluated = evaluate_reading(
                    load=load,
                    indication=indication,
                    e=instrument.scale_interval_e,
                    accuracy_class=instrument.accuracy_class,
                )
                evaluated["kind"] = kind
                evaluated_readings.append(evaluated)
            except Exception:
                continue

        # Compute overall result: passes only if zero_ok and all readings within limit
        passed = is_inspection_passing(zero_ok, evaluated_readings)
        result = InspectionResult.PASS if passed else InspectionResult.FAIL
        target_status = RequestStatus.PASSED if passed else RequestStatus.FAILED

        with db_transaction.atomic():
            inspection = Inspection.objects.create(
                request=req,
                inspector=request.user,
                zero_ok=zero_ok,
                remarks=remarks,
                result=result,
            )

            for item in evaluated_readings:
                TestReading.objects.create(
                    inspection=inspection,
                    kind=item["kind"],
                    test_load=item["load"],
                    indication=item["indication"],
                    error=item["error"],
                    mpe=item["mpe"],
                    within_limit=item["within_limit"],
                )

            note = f"Inspection completed with result {result}. Remarks: {remarks}" if remarks else f"Inspection completed with result {result}."
            transition(req, target_status, actor=request.user, note=note)

        messages.success(request, f"Inspection for Request #{req.pk} submitted: {result}.")
        return redirect("inspector_queue")


class ReadingRowHTMXView(RoleRequiredMixin, View):
    """
    HTMX partial view: adds a reading row or calculates live error and pass/fail dot.
    """
    allowed_roles = [User.Role.INSPECTOR]

    def get(self, request, pk):
        req = get_object_or_404(
            VerificationRequest.objects.filter(
                inspector=request.user,
                status=RequestStatus.ASSIGNED,
            ).select_related("instrument"),
            pk=pk,
        )
        row_id = request.GET.get("row_id", "1")
        return render(request, "verification/partials/reading_row.html", {
            "req": req,
            "row_id": row_id,
            "kinds": ReadingKind.choices,
        })

    def post(self, request, pk):
        req = get_object_or_404(
            VerificationRequest.objects.filter(
                inspector=request.user,
                status=RequestStatus.ASSIGNED,
            ).select_related("instrument"),
            pk=pk,
        )
        instrument = req.instrument

        load_str = request.POST.get("test_load", "0")
        ind_str = request.POST.get("indication", "0")
        row_id = request.POST.get("row_id", "1")
        kind = request.POST.get("kind", ReadingKind.ACCURACY)

        try:
            load = Decimal(load_str)
            indication = Decimal(ind_str)
            evaluated = evaluate_reading(
                load=load,
                indication=indication,
                e=instrument.scale_interval_e,
                accuracy_class=instrument.accuracy_class,
            )
        except Exception:
            evaluated = None

        return render(request, "verification/partials/reading_calc.html", {
            "evaluated": evaluated,
            "row_id": row_id,
            "kind": kind,
        })
