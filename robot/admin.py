from django.contrib import admin
from .models import RobotDelivery


@admin.register(RobotDelivery)
class RobotDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "room",
        "medicine_name",
        "dosage",
        "quantity",
        "status",
        "prepared_by",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "patient__name",
        "patient__patient_id",
        "medicine_name",
        "prepared_by",
    )

    ordering = ("-created_at",)