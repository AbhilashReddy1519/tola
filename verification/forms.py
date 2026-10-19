from django import forms
from django.contrib.auth import get_user_model
from registry.models import Instrument
from .models import VerificationRequest

User = get_user_model()


class VerificationRequestForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ("instrument", "preferred_date", "notes")
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            # Scope instrument choices strictly to the requesting user's business
            self.fields["instrument"].queryset = Instrument.objects.filter(
                business__owner=user
            )


class AssignInspectorForm(forms.ModelForm):
    inspector = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.INSPECTOR, is_active=True),
        required=True,
        empty_label="Select an assigned inspector...",
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Assignment Note",
    )

    class Meta:
        model = VerificationRequest
        fields = ("inspector", "notes")


class InspectionSubmitForm(forms.Form):
    zero_ok = forms.BooleanField(
        required=False,
        initial=True,
        label="Zero Check OK (scale returns to true zero under no load)",
    )
    remarks = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Inspection Remarks",
    )
