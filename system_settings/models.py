
from django.db import models
from django.contrib.auth.models import User


class AdminProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )

    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class HospitalDetails(models.Model):
    HOSPITAL_TYPES = [
        ("General", "General"),
        ("Multispeciality", "Multispeciality"),
        ("Speciality", "Speciality"),
        ("Teaching", "Teaching"),
    ]

    hospital_name = models.CharField(
        max_length=200,
        default="VITACARE Hospital"
    )

    hospital_id = models.CharField(
        max_length=50,
        blank=True
    )

    hospital_type = models.CharField(
        max_length=50,
        choices=HOSPITAL_TYPES,
        blank=True
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True
    )

    address = models.TextField(blank=True)

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(blank=True)

    total_rooms = models.PositiveIntegerField(default=0)

    total_beds = models.PositiveIntegerField(default=0)

    icu_beds = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.hospital_name
