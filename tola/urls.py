from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("app/", include("accounts.app_urls")),
    path("", include("site_pages.urls")),
]
