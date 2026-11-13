
from django.shortcuts import render
from patients.models import Patient, Room
from monitoring.models import VitalReading


def dashboard_home(request):
    total_patients = Patient.objects.count()

    admitted_patients = Patient.objects.filter(
        status="Admitted"
    ).count()

    total_rooms = Room.objects.count()

    available_rooms = Room.objects.filter(
        is_available=True
    ).count()

    recent_patients = (
        Patient.objects
        .select_related("room")
        .order_by("-admission_date")[:5]
    )

    # Find critical patients using their latest recorded readings.
    critical_patients = []

    admitted_list = Patient.objects.filter(
        status="Admitted"
    ).select_related("room")

    for patient in admitted_list:
        reading = (
            VitalReading.objects
            .filter(patient=patient)
            .order_by("-recorded_at")
            .first()
        )

        if reading is None:
            continue

        issues = []

        # These are configurable dashboard alert thresholds,
        # not medical diagnoses.
        if reading.heart_rate > 130 or reading.heart_rate < 40:
            issues.append(
                f"Heart rate: {reading.heart_rate} BPM"
            )

        if reading.spo2 < 90:
            issues.append(
                f"Low SpO2: {reading.spo2}%"
            )

        if reading.temperature >= 39.5 or reading.temperature < 35:
            issues.append(
                f"Abnormal temperature: {reading.temperature} °C"
            )

        if reading.systolic_bp >= 180 or reading.systolic_bp < 80:
            issues.append(
                f"Systolic BP: {reading.systolic_bp} mmHg"
            )

        if reading.diastolic_bp >= 120 or reading.diastolic_bp < 50:
            issues.append(
                f"Diastolic BP: {reading.diastolic_bp} mmHg"
            )
        if reading.iv_level < 15:
            issues.append(
                f"Low IV level: {reading.iv_level}%"
            )

        if issues:
            critical_patients.append({
                "patient": patient,
                "reading": reading,
                "issues": issues,
            })

    context = {
        "total_patients": total_patients,
        "admitted_patients": admitted_patients,
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "recent_patients": recent_patients,
        "critical_patients": critical_patients,
    }

    return render(request, "dashboard.html", context)
