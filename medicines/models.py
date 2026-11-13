from django.db import models
from patients.models import Patient


class Prescription(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Prepared", "Prepared"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    medicine_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1)
    instructions = models.TextField(blank=True)

    prescribed_by = models.CharField(max_length=100)
    prescribed_at = models.DateTimeField(auto_now_add=True)

    prepared_by = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    def __str__(self):
        return f"{self.medicine_name} - {self.patient.name}"