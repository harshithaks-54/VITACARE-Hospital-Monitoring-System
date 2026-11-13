
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, F

from .models import Patient, Room


class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient

        fields = [
            "patient_id",
            "name",
            "age",
            "gender",
            "room",
            "status",
        ]

        widgets = {
            "patient_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter unique patient ID",
            }),

            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter patient's full name",
            }),

            "age": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter age",
                "min": 1,
            }),

            "gender": forms.Select(attrs={
                "class": "form-control",
            }),

            "room": forms.Select(attrs={
                "class": "form-control",
            }),

            "status": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        available_rooms = Room.objects.annotate(
            admitted_patient_count=Count(
                "patients",
                filter=Q(patients__status="Admitted")
            )
        ).filter(
            admitted_patient_count__lt=F("bed_capacity")
        )

        # Keep the patient's existing room available while editing.
        if self.instance and self.instance.pk and self.instance.room_id:
            available_rooms = Room.objects.annotate(
                admitted_patient_count=Count(
                    "patients",
                    filter=Q(patients__status="Admitted")
                )
            ).filter(
                Q(admitted_patient_count__lt=F("bed_capacity"))
                | Q(pk=self.instance.room_id)
            )

        self.fields["room"].queryset = available_rooms.order_by(
            "room_number"
        )

    def clean_patient_id(self):
        patient_id = self.cleaned_data["patient_id"].strip()

        existing = Patient.objects.filter(
            patient_id__iexact=patient_id
        )

        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError(
                "This Patient ID is already registered. Please use another ID."
            )

        return patient_id

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())

        existing = Patient.objects.filter(
            name__iexact=name
        )

        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise ValidationError(
                "A patient with this name is already registered. "
                "Please check the existing patient records."
            )

        return name

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        age = cleaned_data.get("age")
        gender = cleaned_data.get("gender")

        if name and age is not None and gender:
            duplicate = Patient.objects.filter(
                name__iexact=name,
                age=age,
                gender=gender
            )

            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)

            if duplicate.exists():
                raise ValidationError(
                    "A patient with exactly the same details already exists."
                )

        return cleaned_data
