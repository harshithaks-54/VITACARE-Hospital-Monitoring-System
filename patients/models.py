
from django.db import models
from django.core.exceptions import ValidationError


class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    floor = models.PositiveIntegerField(default=1)
    bed_capacity = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)

    @property
    def occupied_beds(self):
        return self.patients.filter(status="Admitted").count()

    @property
    def available_beds(self):
        return max(0, self.bed_capacity - self.occupied_beds)

    @property
    def occupancy_percentage(self):
        if self.bed_capacity == 0:
            return 0

        percentage = (self.occupied_beds / self.bed_capacity) * 100
        return min(100, round(percentage))

    def clean(self):
        if self.bed_capacity < 1:
            raise ValidationError({
                "bed_capacity": "Bed capacity must be at least 1."
            })

        if self.pk:
            current_occupancy = self.patients.filter(
                status="Admitted"
            ).count()

            if current_occupancy > self.bed_capacity:
                raise ValidationError({
                    "bed_capacity": (
                        f"This room already has {current_occupancy} "
                        f"admitted patients. Capacity cannot be "
                        f"reduced below the occupied beds."
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Room {self.room_number}"


class Patient(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("Admitted", "Admitted"),
        ("Discharged", "Discharged"),
    ]

    patient_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients"
    )

    admission_date = models.DateField(auto_now_add=True)

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="Admitted"
    )

    def clean(self):
        if self.status == "Admitted" and self.room_id:
            existing_patients = Patient.objects.filter(
                room_id=self.room_id,
                status="Admitted"
            )

            if self.pk:
                existing_patients = existing_patients.exclude(
                    pk=self.pk
                )

            occupied = existing_patients.count()

            if occupied >= self.room.bed_capacity:
                raise ValidationError({
                    "room": (
                        f"Room {self.room.room_number} is full. "
                        f"Bed capacity: {self.room.bed_capacity}, "
                        f"occupied beds: {occupied}. "
                        "Please select another available room."
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.name}"
