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

    def get_queryset(self):
        business = get_user_business(self.request.user)
        if not business:
            return Instrument.objects.none()
        return (
            Instrument.objects.filter(business=business)
            .select_related("business", "business__owner")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["business"] = get_user_business(self.request.user)
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
