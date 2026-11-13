import csv

from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models import Count, Q, OuterRef, Exists
from django.db.models.functions import TruncDate

from patients.models import Patient, Room
from monitoring.models import VitalReading, PatientAlert
from robot.models import RobotDelivery


def reports_dashboard(request):

    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))
    selected_view = request.GET.get("view", "")

    # Reject an invalid date range.
    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date

    # PATIENTS
    patients = Patient.objects.select_related("room").all()

    if start_date:
        patients = patients.filter(admission_date__gte=start_date)

    if end_date:
        patients = patients.filter(admission_date__lte=end_date)

    patient_stats = patients.aggregate(
        total=Count("id"),
        admitted=Count("id", filter=Q(status="Admitted")),
        discharged=Count("id", filter=Q(status="Discharged")),
    )

    # ROOMS
    rooms = Room.objects.all()

    room_stats = rooms.aggregate(
        total=Count("id"),
        available=Count("id", filter=Q(is_available=True)),
        occupied=Count("id", filter=Q(is_available=False)),
    )

    # DELIVERIES
    deliveries = RobotDelivery.objects.select_related(
        "patient", "room"
    ).all()

    if start_date:
        deliveries = deliveries.filter(
            created_at__date__gte=start_date
        )

    if end_date:
        deliveries = deliveries.filter(
            created_at__date__lte=end_date
        )

    delivery_stats = deliveries.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status="Collected")),
        in_progress=Count(
            "id",
            filter=Q(status__in=[
                "Order Received", "Dispatched", "Arrived"
            ])
        ),
        cancelled=Count("id", filter=Q(status="Cancelled")),
    )

    # MONITORING
    readings = VitalReading.objects.select_related("patient").all()
    alerts = PatientAlert.objects.select_related(
        "patient", "vital_reading"
    ).all()

    if start_date:
        readings = readings.filter(recorded_at__date__gte=start_date)
        alerts = alerts.filter(created_at__date__gte=start_date)

    if end_date:
        readings = readings.filter(recorded_at__date__lte=end_date)
        alerts = alerts.filter(created_at__date__lte=end_date)

    # A reading is counted as "without alerts" only if no alert
    # exists for that reading, regardless of the alert's status.
    reading_alerts = PatientAlert.objects.filter(
        vital_reading_id=OuterRef("pk")
    )

    readings_without_alerts = readings.annotate(
        has_alert=Exists(reading_alerts)
    ).filter(has_alert=False)

    monitoring_stats = {
        "total_readings": readings.count(),
        "critical_alerts": alerts.filter(
            severity="Critical",
            status="Active"
        ).count(),
        "normal_readings": readings_without_alerts.count(),
    }

    # DELIVERY TREND: one grouped query, not seven separate queries.
    today = timezone.localdate()

    if start_date or end_date:
        trend_start = start_date or (end_date - timezone.timedelta(days=6))
        trend_end = end_date or today
    else:
        trend_start = today - timezone.timedelta(days=6)
        trend_end = today

    trend_queryset = deliveries.filter(
        created_at__date__gte=trend_start,
        created_at__date__lte=trend_end
    )

    trend_counts = {
        item["day"].strftime("%d %b"): item["count"]
        for item in trend_queryset
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    }

    trend_data = []
    current_day = trend_start

    while current_day <= trend_end:
        label = current_day.strftime("%d %b")
        trend_data.append({
            "date": label,
            "count": trend_counts.get(label, 0),
        })
        current_day += timezone.timedelta(days=1)

    # DETAIL VIEW
    detail_title = ""
    detail_type = ""
    detail_queryset = None

    detail_map = {
        "patients": ("All Patient Records", "patients", patients),
        "admitted": (
            "Admitted Patients", "patients",
            patients.filter(status="Admitted")
        ),
        "discharged": (
            "Discharged Patients", "patients",
            patients.filter(status="Discharged")
        ),
        "rooms": ("All Hospital Rooms", "rooms", rooms),
        "available": (
            "Available Rooms", "rooms",
            rooms.filter(is_available=True)
        ),
        "occupied": (
            "Occupied Rooms", "rooms",
            rooms.filter(is_available=False)
        ),
        "deliveries": (
            "All Medicine Deliveries", "deliveries", deliveries
        ),
        "completed": (
            "Completed Deliveries", "deliveries",
            deliveries.filter(status="Collected")
        ),
        "in_progress": (
            "Deliveries In Progress", "deliveries",
            deliveries.filter(status__in=[
                "Order Received", "Dispatched", "Arrived"
            ])
        ),
        "cancelled": (
            "Cancelled Deliveries", "deliveries",
            deliveries.filter(status="Cancelled")
        ),
        "readings": (
            "Patient Monitoring Readings", "readings", readings
        ),
        "critical": (
            "Active Critical Alerts", "alerts",
            alerts.filter(severity="Critical", status="Active")
        ),
        "normal": (
            "Readings Without Recorded Alerts", "readings",
            readings_without_alerts
        ),
    }

    if selected_view in detail_map:
        detail_title, detail_type, detail_queryset = detail_map[selected_view]

    # CSV EXPORT
    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="vitacare_delivery_report.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            "Delivery ID", "Patient", "Patient ID", "Room",
            "Medicine", "Dosage", "Quantity", "Prepared By",
            "Status", "Created At", "Dispatched At", "Collected At"
        ])

        for delivery in deliveries.order_by("-created_at").iterator():
            writer.writerow([
                delivery.id,
                delivery.patient.name,
                delivery.patient.patient_id,
                delivery.room.room_number,
                delivery.medicine_name,
                delivery.dosage,
                delivery.quantity,
                delivery.prepared_by,
                delivery.status,
                delivery.created_at,
                delivery.dispatched_at or "",
                delivery.collected_at or "",
            ])

        return response

    # Limit detail records to avoid loading huge tables.
    detail_count = detail_queryset.count() if detail_queryset is not None else 0

    if detail_queryset is not None:
        if detail_type == "patients":
            detail_queryset = detail_queryset.order_by("-admission_date")
        elif detail_type == "rooms":
            detail_queryset = detail_queryset.order_by("room_number")
        elif detail_type == "deliveries":
            detail_queryset = detail_queryset.order_by("-created_at")
        elif detail_type == "readings":
            detail_queryset = detail_queryset.order_by("-recorded_at")
        elif detail_type == "alerts":
            detail_queryset = detail_queryset.order_by("-created_at")

        detail_records = detail_queryset[:100]
    else:
        detail_records = []

    context = {
        "patient_stats": patient_stats,
        "room_stats": room_stats,
        "delivery_stats": delivery_stats,
        "monitoring_stats": monitoring_stats,
        "trend_data": trend_data,
        "delivery_distribution": {
            "completed": delivery_stats["completed"],
            "in_progress": delivery_stats["in_progress"],
            "cancelled": delivery_stats["cancelled"],
        },
        "recent_deliveries": deliveries.order_by("-created_at")[:8],
        "detail_title": detail_title,
        "detail_type": detail_type,
        "detail_records": detail_records,
        "detail_count": detail_count,
        "has_more_records": detail_count > 100,
        "selected_view": selected_view,
        "start_date": start_date,
        "end_date": end_date,
        "report_date": today,
    }

    return render(request, "reports.html", context)