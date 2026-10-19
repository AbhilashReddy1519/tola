from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from .forms import LoginForm, OwnerRegistrationForm
from .mixins import RoleRequiredMixin
from .models import User


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("app_redirect")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("landing")

    def get(self, request, *args, **kwargs):
        """Allow GET for easy logout while still supporting POST."""
        return self.post(request, *args, **kwargs)


class OwnerRegistrationView(CreateView):
    form_class = OwnerRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("app_redirect")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = User.Role.OWNER
        user.save()
        login(self.request, user)
        return redirect(self.success_url)


class RoleDashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        role = getattr(request.user, "role", None)
        if role == User.Role.OWNER:
            return redirect("instrument_list")
        elif role == User.Role.INSPECTOR:
            return redirect("inspector_queue")
        elif role == User.Role.ADMIN:
            return redirect("admin_console")
        raise PermissionDenied("Unrecognized user role.")


class OwnerDashboardStubView(RoleRequiredMixin, TemplateView):
    allowed_roles = [User.Role.OWNER]
    template_name = "accounts/owner_dashboard.html"


class InspectorQueueStubView(RoleRequiredMixin, TemplateView):
    allowed_roles = [User.Role.INSPECTOR]
    template_name = "accounts/inspector_queue.html"


class AdminConsoleStubView(RoleRequiredMixin, TemplateView):
    allowed_roles = [User.Role.ADMIN]
    template_name = "accounts/admin_console.html"
