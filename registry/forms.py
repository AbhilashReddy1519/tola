from django import forms
from .models import Business, Instrument


class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = (
            "name",
            "trade_type",
            "address",
            "district",
            "pincode",
            "licence_no",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class InstrumentForm(forms.ModelForm):
    class Meta:
        model = Instrument
        fields = (
            "category",
            "make",
            "model_no",
            "serial_no",
            "max_capacity",
            "unit",
            "scale_interval_e",
            "accuracy_class",
            "installed_on",
        )
        widgets = {
            "installed_on": forms.DateInput(attrs={"type": "date"}),
        }
