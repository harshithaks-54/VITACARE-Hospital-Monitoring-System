
from django.db import models
from patients.models import Patient


class VitalReading(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="vital_readings"
    )

    heart_rate = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    spo2 = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    temperature = models.FloatField(
        null=True,
        blank=True
    )

    systolic_bp = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    diastolic_bp = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    iv_level = models.FloatField(
        null=True,
        blank=True
    )

    recorded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Vitals for {self.patient.patient_id} at {self.recorded_at}"

class PatientAlert(models.Model):

    SEVERITY_CHOICES = [
        ("Critical", "Critical"),
        ("Warning", "Warning"),
    ]

    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Acknowledged", "Acknowledged"),
        ("Resolved", "Resolved"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="alerts"
    )

    vital_reading = models.ForeignKey(
        VitalReading,
        on_delete=models.CASCADE,
        related_name="alerts"
    )

    parameter = models.CharField(max_length=50)

    message = models.TextField()

    severity = models.CharField(
        max_length=15,
        choices=SEVERITY_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Active"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.patient.patient_id} - {self.parameter} - {self.severity}"
