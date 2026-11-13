from django.contrib import admin
from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "medicine_name",
        "dosage",
        "quantity",
        "prescribed_by",
        "status",
        "prescribed_at",
    )

    list_filter = ("status", "prescribed_at")
    search_fields = ("patient__name", "medicine_name")