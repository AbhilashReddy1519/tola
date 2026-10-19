from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from .forms import BusinessForm, InstrumentForm
from .models import Business, Instrument

User = get_user_model()


def get_user_business(user):
    """Return the single business owned by the user for the MVP."""
    return Business.objects.filter(owner=user).first()


class BusinessCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.Role.OWNER]
    model = Business
    form_class = BusinessForm
    template_name = "registry/business_form.html"
    success_url = reverse_lazy("instrument_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and get_user_business(request.user):
            return redirect("business_edit")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class BusinessUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.Role.OWNER]
    model = Business
    form_class = BusinessForm
    template_name = "registry/business_form.html"
    success_url = reverse_lazy("instrument_list")

    def get_object(self, queryset=None):
        return get_object_or_404(Business.objects.filter(owner=self.request.user))


class InstrumentListView(RoleRequiredMixin, ListView):
    allowed_roles = [User.Role.OWNER]
    model = Instrument
    template_name = "registry/instrument_list.html"
    context_object_name = "instruments"

    def get_business(self):
        if not hasattr(self, "_cached_business"):
            self._cached_business = get_user_business(self.request.user)
        return self._cached_business

    def get_queryset(self):
        business = self.get_business()
        if not business:
            return Instrument.objects.none()
        return (
            Instrument.objects.filter(business=business)
            .select_related("business", "business__owner")
            .prefetch_related(
                "verification_requests",
                "verification_requests__inspection__certificate",
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_business()
        context["business"] = business

        from django.utils import timezone
        now = timezone.localtime()
        if now.hour < 12:
            greeting_prefix = "Good morning"
        elif now.hour < 17:
            greeting_prefix = "Good afternoon"
        else:
            greeting_prefix = "Good evening"

        user = self.request.user
        owner_name = user.first_name.strip() if user.first_name else user.username
        # Capitalize nicely if lowercase username
        if not user.first_name and "_" in owner_name:
            owner_name = owner_name.split("_")[-1].capitalize()
        context["greeting"] = f"{greeting_prefix}, {owner_name}."

        instruments = list(context["instruments"])
        valid_count = 0
        expiring_count = 0
        overdue_count = 0
        deadlines = []
        today = timezone.now().date()

        for inst in instruments:
            st = inst.status
            if st == "Valid":
                valid_count += 1
            elif st == "Expiring soon":
                expiring_count += 1
            elif st in ["Expired", "Failed", "Revoked", "Unverified"]:
                overdue_count += 1

            cert = inst.current_certificate
            if cert and cert.valid_until and cert.is_valid:
                days_left = (cert.valid_until - today).days
                deadlines.append({
                    "instrument": inst,
                    "date": cert.valid_until,
                    "days_left": days_left,
                    "cert": cert,
                })

        deadlines.sort(key=lambda d: d["date"])
        context["valid_count"] = valid_count
        context["expiring_count"] = expiring_count
        context["overdue_count"] = overdue_count
        context["deadlines"] = deadlines[:3]
        return context


class InstrumentDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = [User.Role.OWNER]
    model = Instrument
    template_name = "registry/instrument_detail.html"
    context_object_name = "instrument"

    def get_queryset(self):
        # Strict scoping: query only instruments belonging to request.user's business
        business = get_user_business(self.request.user)
        if not business:
            return Instrument.objects.none()
        return (
            Instrument.objects.filter(business=business)
            .select_related("business", "business__owner")
        )


class InstrumentCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = [User.Role.OWNER]
    model = Instrument
    form_class = InstrumentForm
    template_name = "registry/instrument_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not get_user_business(request.user):
            return redirect("business_create")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.business = get_user_business(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("instrument_detail", kwargs={"pk": self.object.pk})


class InstrumentUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = [User.Role.OWNER]
    model = Instrument
    form_class = InstrumentForm
    template_name = "registry/instrument_form.html"

    def get_queryset(self):
        # Strict scoping: query only instruments belonging to request.user's business
        business = get_user_business(self.request.user)
        if not business:
            return Instrument.objects.none()
        return (
            Instrument.objects.filter(business=business)
            .select_related("business", "business__owner")
        )

    def get_success_url(self):
        return reverse("instrument_detail", kwargs={"pk": self.object.pk})
