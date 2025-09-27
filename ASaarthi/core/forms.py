# core/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import SymptomReport

# ----------------------------
# USER REGISTRATION FORM
# ----------------------------
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_password2(self):
        """Ensure that password1 and password2 match."""
        cd = self.cleaned_data
        if cd.get('password1') != cd.get('password2'):
            raise forms.ValidationError("Passwords don't match.")
        return cd.get('password2')


# ----------------------------
# LOGIN FORM
# ----------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")


# ----------------------------
# SYMPTOM REPORT FORM
# ----------------------------
class SymptomReportForm(forms.ModelForm):
    class Meta:
        model = SymptomReport
        fields = [
            "name", "age", "gender", "contact",
            "village", "state", "district",
            "symptoms", "disease", "water_source",
            "image", "remarks"
        ]
