
from django.contrib import admin
from .models import VitalReading


@admin.register(VitalReading)
class VitalReadingAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "heart_rate",
        "spo2",
        "temperature",
        "systolic_bp",
        "diastolic_bp",
        "iv_level",
        "recorded_at",
    )

    list_filter = ("recorded_at",)
    search_fields = ("patient__patient_id", "patient__name")
    ordering = ("-recorded_at",)
