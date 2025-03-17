from django import forms
from .models import Refugee, CustomUser
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

CustomUser = get_user_model()  # Use the swapped user model
# Login Form
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

# Sign-Up Form
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = CustomUser
        fields = ("email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # Set username as email
        if commit:
            user.save()
        return user
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.pop('autofocus', None)  # Remove autofocus forcefully


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
            "full_name": forms.TextInput(attrs={"class": "form-control", "id": "full-name"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "id": "dob", "type": "date"}),
            "gender": forms.Select(attrs={"class": "form-select", "id": "gender"}),
            "nationality": forms.TextInput(attrs={"class": "form-control", "id": "nationality"}),
            "language_spoken": forms.TextInput(attrs={"class": "form-control", "id": "language"}),
            "refugee_status": forms.Select(attrs={"class": "form-select", "id": "status"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "id": "phone"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "email"}),
            "location": forms.TextInput(attrs={"class": "form-control", "id": "location"}),
            "fingerprint_data": forms.HiddenInput(),
        }

