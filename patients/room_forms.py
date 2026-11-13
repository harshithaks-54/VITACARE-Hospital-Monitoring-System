
from django import forms
from .models import Room


class RoomForm(forms.ModelForm):

    class Meta:
        model = Room
        fields = [
            "room_number",
            "floor",
            "bed_capacity",
        ]

        widgets = {
            "room_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter room number",
            }),

            "floor": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter floor number",
                "min": 1,
            }),

            "bed_capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter total beds",
                "min": 1,
            }),
        }

    def clean_room_number(self):
        room_number = self.cleaned_data["room_number"].strip()

        existing = Room.objects.filter(
            room_number__iexact=room_number
        )

        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError(
                "This room number already exists. Please enter another room number."
            )

        return room_number

    def clean_floor(self):
        floor = self.cleaned_data["floor"]

        if floor < 1:
            raise forms.ValidationError("Floor number must be at least 1.")

        return floor

    def clean_bed_capacity(self):
        capacity = self.cleaned_data["bed_capacity"]

        if capacity < 1:
            raise forms.ValidationError("A room must have at least one bed.")

        return capacity
