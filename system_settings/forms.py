
from django import forms
from django.contrib.auth.models import User

from .models import AdminProfile, HospitalDetails


# --------------------------------------------------
# ADMIN PROFILE FORM
# --------------------------------------------------

class AdminProfileForm(forms.ModelForm):

    full_name = forms.CharField(
        max_length=150,
        required=False,
        label="Full Name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter administrator name",
        })
    )

    email = forms.EmailField(
        required=False,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email address",
        })
    )

    class Meta:
        model = AdminProfile
        fields = ["phone_number", "department"]

        widgets = {
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter phone number",
            }),
            "department": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter department",
            }),
        }


# --------------------------------------------------
# USER MANAGEMENT FORM
# --------------------------------------------------

class UserManagementForm(forms.ModelForm):

    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Doctor", "Doctor"),
        ("Nurse", "Nurse"),
        ("Pharmacist", "Pharmacist"),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            "class": "form-select",
        })
    )

    password = forms.CharField(
        required=False,
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password",
        })
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
        ]

        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter username",
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter first name",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter last name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter email address",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")

        existing_users = User.objects.filter(username=username)

        if self.instance and self.instance.pk:
            existing_users = existing_users.exclude(pk=self.instance.pk)

        if existing_users.exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if not self.instance or not self.instance.pk:
            if not password:
                raise forms.ValidationError(
                    "Password is required when creating a new user."
                )

        return password


# --------------------------------------------------
# HOSPITAL DETAILS FORM
# --------------------------------------------------

class HospitalDetailsForm(forms.ModelForm):

    class Meta:
        model = HospitalDetails

        fields = [
            "hospital_name",
            "hospital_id",
            "hospital_type",
            "registration_number",
            "address",
            "phone_number",
            "email",
            "total_rooms",
            "total_beds",
            "icu_beds",
        ]

        widgets = {
            "hospital_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter hospital name",
            }),
            "hospital_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter hospital ID",
            }),
            "hospital_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "registration_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter registration number",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter hospital address",
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter hospital phone number",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Enter hospital email",
            }),
            "total_rooms": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
            }),
            "total_beds": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
            }),
            "icu_beds": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        total_beds = cleaned_data.get("total_beds")
        icu_beds = cleaned_data.get("icu_beds")

        if (
            total_beds is not None
            and icu_beds is not None
            and icu_beds > total_beds
        ):
            self.add_error(
                "icu_beds",
                "ICU beds cannot exceed total beds."
            )

        return cleaned_data
