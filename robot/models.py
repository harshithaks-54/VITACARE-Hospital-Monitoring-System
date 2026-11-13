
from django.db import models
from patients.models import Patient, Room


class RobotDelivery(models.Model):

    STATUS_CHOICES = [
        ("Order Received", "Order Received"),
        ("Dispatched", "Dispatched"),
        ("Arrived", "Arrived"),
        ("Collected", "Collected"),
        ("Cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="robot_deliveries"
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name="robot_deliveries"
    )

    # Medicine details entered by the nurse
    medicine_name = models.CharField(max_length=150,blank=True,default="")
    dosage = models.CharField(max_length=100,blank=True,default="")
    quantity = models.PositiveIntegerField(default=1)

    prepared_by = models.CharField(max_length=100, blank=True)

    verification_method = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ("RFID", "RFID"),
            ("PIN", "PIN"),
        ]
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Order Received"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery {self.id} - {self.patient.name}"
