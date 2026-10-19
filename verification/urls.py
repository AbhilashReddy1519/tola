from django.urls import path
from . import views

urlpatterns = [
    # Owner routes
    path("requests/", views.OwnerRequestListView.as_view(), name="owner_request_list"),
    path("requests/new/", views.OwnerRequestCreateView.as_view(), name="owner_request_create"),
    path("requests/<int:pk>/", views.OwnerRequestDetailView.as_view(), name="owner_request_detail"),
    path("requests/<int:pk>/cancel/", views.OwnerRequestCancelView.as_view(), name="owner_request_cancel"),

    # Admin routes
    path("console/requests/", views.AdminConsoleRequestListView.as_view(), name="admin_request_list"),
    path("console/requests/<int:pk>/assign/", views.AdminAssignInspectorView.as_view(), name="admin_request_assign"),

    # Inspector routes
    path("inspector/queue/", views.InspectorQueueView.as_view(), name="inspector_queue"),
    path("inspector/requests/<int:pk>/inspect/", views.InspectorInspectionView.as_view(), name="inspector_inspect"),
    path("inspector/requests/<int:pk>/reading-row/", views.ReadingRowHTMXView.as_view(), name="inspector_reading_row"),
]
