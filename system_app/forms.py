from django import forms
from .models import Refugee

class RefugeeRegistrationForm(forms.ModelForm):
    class Meta:
        model = Refugee
        fields = [
            "full_name",
            "date_of_birth",
            "gender",
            "nationality",
            "language_spoken",
            "refugee_status",
            "phone_number",
            "email",
            "location",
            "fingerprint_data",
        ]
        widgets = {
            "fingerprint_data": forms.HiddenInput(),
        }

