from django.urls import path

from . import views

urlpatterns = [
    path("", views.RoleDashboardRedirectView.as_view(), name="app_redirect"),
    path("owner/", views.OwnerDashboardStubView.as_view(), name="owner_dashboard"),
    path("instruments/", views.OwnerDashboardStubView.as_view(), name="owner_instruments_stub"),
    path("inspector/queue/", views.InspectorQueueStubView.as_view(), name="inspector_queue"),
    path("console/", views.AdminConsoleStubView.as_view(), name="admin_console"),
    path("console/requests/", views.AdminConsoleStubView.as_view(), name="admin_requests_stub"),
]
