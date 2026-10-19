from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class OwnerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email address")
    phone = forms.CharField(max_length=20, required=False, label="Phone number")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "phone")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.OWNER
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    pass
