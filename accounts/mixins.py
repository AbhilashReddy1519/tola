from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(AccessMixin):
    """
    Mixin that restricts access to users with specific roles.
    If the user is not authenticated, redirects to the login URL.
    If the user is authenticated but does not possess an allowed role, returns 403.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        allowed = [
            role.value if hasattr(role, "value") else str(role)
            for role in self.allowed_roles
        ]
        user_role = getattr(request.user, "role", None)

        if user_role not in allowed:
            raise PermissionDenied("You do not have permission to access this resource.")

        return super().dispatch(request, *args, **kwargs)
