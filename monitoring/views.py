
from random import randint
from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from patients.models import Patient
from .models import VitalReading, PatientAlert



def monitoring_page(request):

    patients = (
        Patient.objects
        .filter(status="Admitted")
        .select_related("room")
        .order_by("name")
    )

    selected_id = request.GET.get("patient")
    demo_mode = request.GET.get("demo") == "1"

    selected_patient = None

    if selected_id:
        selected_patient = patients.filter(
            pk=selected_id
        ).first()

    if selected_patient is None:
        selected_patient = patients.first()

    patient_data = []

    for patient in patients:

        latest = (
            VitalReading.objects
            .filter(patient=patient)
            .order_by("-recorded_at")
            .first()
        )

        if demo_mode:

            # Simulated readings for interface testing.
            # These values are not saved in MySQL.

            reading = {
                "heart_rate": randint(65, 145),
                "spo2": randint(86, 100),
                "temperature": round(randint(365, 400) / 10, 1),
                "systolic_bp": randint(100, 180),
                "diastolic_bp": randint(60, 115),
                "iv_level": randint(5, 100),
                "recorded_at": timezone.now(),
            }

        elif latest:

            reading = {
                "heart_rate": latest.heart_rate,
                "spo2": latest.spo2,
                "temperature": latest.temperature,
                "systolic_bp": latest.systolic_bp,
                "diastolic_bp": latest.diastolic_bp,
                "iv_level": latest.iv_level,
                "recorded_at": latest.recorded_at,
            }

        else:
            reading = None

        patient_data.append({
            "patient": patient,
            "reading": reading,
        })

    # Find the selected patient's readings
    selected_data = None

    if selected_patient:
        selected_data = next(
            (
                item for item in patient_data
                if item["patient"].pk == selected_patient.pk
            ),
            None
        )

    # Prepare historical readings for the trend chart
    trend_readings = []

    if selected_patient and selected_data and selected_data["reading"]:

        if demo_mode:

            # Generate seven simulated trend points.
            # The last point matches the current displayed reading.

            current = selected_data["reading"]

            for i in range(7):

                if i == 6:
                    trend_readings.append({
                        "time": current["recorded_at"].strftime("%H:%M"),
                        "heart_rate": current["heart_rate"],
                        "spo2": current["spo2"],
                        "systolic_bp": current["systolic_bp"],
                    })

                else:
                    recorded_time = (
                        current["recorded_at"]
                        - timedelta(minutes=(6 - i) * 5)
                    )

                    trend_readings.append({
                        "time": recorded_time.strftime("%H:%M"),
                        "heart_rate": randint(65, 110),
                        "spo2": randint(94, 100),
                        "systolic_bp": randint(105, 140),
                    })

        else:

            # Fetch the latest seven actual saved database readings.
            history = (
                VitalReading.objects
                .filter(patient=selected_patient)
                .order_by("-recorded_at")[:7]
            )

            history = list(reversed(history))

            for item in history:

                trend_readings.append({
                    "time": timezone.localtime(
                        item.recorded_at
                    ).strftime("%H:%M"),

                    "heart_rate": item.heart_rate,
                    "spo2": item.spo2,
                    "systolic_bp": item.systolic_bp,
                })

    context = {
        "patient_data": patient_data,
        "selected_patient": selected_patient,
        "selected_data": selected_data,
        "total_monitored": len(patient_data),
        "demo_mode": demo_mode,
        "trend_readings": trend_readings,
    }

    return render(request, "monitoring.html", context)

def check_patient_alerts():

    patients = Patient.objects.filter(status="Admitted")

    for patient in patients:

        latest = (
            VitalReading.objects
            .filter(patient=patient)
            .order_by("-recorded_at")
            .first()
        )

        if not latest:
            continue

        readings = [
            ("Heart Rate", latest.heart_rate, "bpm", 50, 120, 40, 130),
            ("SpO2", latest.spo2, "%", 94, None, 90, None),
            ("Temperature", latest.temperature, "°C", 38, None, 35, 39.5),
            ("Systolic BP", latest.systolic_bp, "mmHg", 90, 140, 80, 180),
            ("Diastolic BP", latest.diastolic_bp, "mmHg", 60, 90, 50, 120),
            ("IV Level", latest.iv_level, "%", 20, None, 10, None),
        ]

        for parameter, value, unit, low_warn, high_warn, low_critical, high_critical in readings:

            if value is None:
                continue

            critical = (
                (low_critical is not None and value < low_critical)
                or
                (high_critical is not None and value > high_critical)
            )

            warning = (
                (low_warn is not None and value < low_warn)
                or
                (high_warn is not None and value > high_warn)
            )

            if critical:
                severity = "Critical"

            elif warning:
                severity = "Warning"

            else:
                continue

            message = (
                f"{parameter} reading is {value} {unit} "
                f"for patient {patient.name}."
            )

            PatientAlert.objects.get_or_create(
                patient=patient,
                vital_reading=latest,
                parameter=parameter,
                defaults={
                    "message": message,
                    "severity": severity,
                    "status": "Active",
                }
            )

def alerts_page(request):

    check_patient_alerts()

    alerts = PatientAlert.objects.select_related(
        "patient",
        "vital_reading"
    ).order_by("-created_at")

    active_alerts = alerts.filter(status="Active")

    # Read the selected card filter
    selected_filter = request.GET.get("filter", "all")

    # Filter alerts based on the selected card
    if selected_filter == "critical":
        displayed_alerts = active_alerts.filter(
            severity="Critical"
        )

    elif selected_filter == "warning":
        displayed_alerts = active_alerts.filter(
            severity="Warning"
        )

    else:
        selected_filter = "all"
        displayed_alerts = active_alerts

    context = {
        "alerts": displayed_alerts,
        "active_alerts": active_alerts,

        "total_alerts": active_alerts.count(),

        "critical_count": active_alerts.filter(
            severity="Critical"
        ).count(),

        "warning_count": active_alerts.filter(
            severity="Warning"
        ).count(),

        "selected_filter": selected_filter,
    }

    return render(request, "alerts.html", context)





