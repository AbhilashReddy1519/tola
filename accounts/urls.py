from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.OwnerRegistrationView.as_view(), name="register"),
]
