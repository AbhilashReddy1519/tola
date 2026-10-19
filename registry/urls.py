from django.urls import path
from . import views

urlpatterns = [
    path("instruments/", views.InstrumentListView.as_view(), name="instrument_list"),
    path("instruments/new/", views.InstrumentCreateView.as_view(), name="instrument_create"),
    path("instruments/<int:pk>/", views.InstrumentDetailView.as_view(), name="instrument_detail"),
    path("instruments/<int:pk>/edit/", views.InstrumentUpdateView.as_view(), name="instrument_edit"),
    path("business/new/", views.BusinessCreateView.as_view(), name="business_create"),
    path("business/edit/", views.BusinessUpdateView.as_view(), name="business_edit"),
]
