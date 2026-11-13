
from django.contrib import admin
from .models import Patient, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "room_number",
        "floor",
        "bed_capacity",
        "is_available",
    )
    search_fields = ("room_number",)
    list_filter = ("floor", "is_available")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "patient_id",
        "name",
        "age",
        "gender",
        "room",
        "status",
        "admission_date",
    )
    search_fields = ("patient_id", "name")
    list_filter = ("gender", "status", "room")
