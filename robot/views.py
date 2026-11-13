
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.contrib import messages

from patients.models import Patient
from .models import RobotDelivery


def robot_dashboard(request):

    patients = Patient.objects.filter(
        status="Admitted"
    ).select_related("room").order_by("name")

    deliveries = RobotDelivery.objects.select_related(
        "patient", "room"
    ).order_by("-created_at")

    today = timezone.localdate()

    today_deliveries = deliveries.filter(
        created_at__date=today
    )

    completed_deliveries = today_deliveries.filter(
        status="Collected"
    )

    in_progress = today_deliveries.filter(
        status__in=["Order Received", "Dispatched", "Arrived"]
    )

    latest_delivery = deliveries.exclude(
        status="Cancelled"
    ).first()

    context = {
        "patients": patients,
        "deliveries": deliveries[:20],

        "today_deliveries_count": today_deliveries.count(),
        "completed_count": completed_deliveries.count(),
        "in_progress_count": in_progress.count(),

        "latest_delivery": latest_delivery,

        "robot_status": (
            "Delivering" if in_progress.exists() else "Idle"
        ),

        "battery_level": 85,
        "navigation_mode": "Line Following (Simulation)",
        "current_location": "Charging Station",
        "simulation_mode": True,
    }

    return render(request, "robot.html", context)


@require_GET
def patient_details(request, patient_id):

    patient = get_object_or_404(
        Patient.objects.select_related("room"),
        pk=patient_id,
        status="Admitted"
    )

    return JsonResponse({
        "success": True,
        "patient": patient.name,
        "patient_id": patient.patient_id,
        "room": (
            patient.room.room_number
            if patient.room else "Not assigned"
        ),
        "has_room": bool(patient.room),
    })


@require_POST
def create_delivery(request):

    patient_id = request.POST.get("patient_id")
    medicine_name = request.POST.get("medicine_name", "").strip()
    dosage = request.POST.get("dosage", "").strip()
    quantity = request.POST.get("quantity", "").strip()
    prepared_by = request.POST.get("prepared_by", "").strip()

    if not all([
        patient_id,
        medicine_name,
        dosage,
        quantity,
        prepared_by
    ]):
        messages.error(
            request,
            "Please enter all delivery details."
        )
        return redirect("robot_dashboard")

    try:
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError

    except ValueError:
        messages.error(
            request,
            "Medicine quantity must be a positive number."
        )
        return redirect("robot_dashboard")

    patient = get_object_or_404(
        Patient.objects.select_related("room"),
        pk=patient_id,
        status="Admitted"
    )

    if not patient.room:
        messages.error(
            request,
            "This patient does not have an assigned room."
        )
        return redirect("robot_dashboard")

    active_delivery = RobotDelivery.objects.filter(
        patient=patient,
        status__in=[
            "Order Received",
            "Dispatched",
            "Arrived"
        ]
    ).exists()

    if active_delivery:
        messages.error(
            request,
            "This patient already has an active delivery."
        )
        return redirect("robot_dashboard")

    RobotDelivery.objects.create(
        patient=patient,
        room=patient.room,
        medicine_name=medicine_name,
        dosage=dosage,
        quantity=quantity,
        prepared_by=prepared_by,
        status="Order Received"
    )

    messages.success(
        request,
        "Medicine delivery order created successfully."
    )

    return redirect("robot_dashboard")


@require_POST
def delivery_action(request, delivery_id):

    delivery = get_object_or_404(
        RobotDelivery,
        pk=delivery_id
    )

    action = request.POST.get("action")

    if action == "dispatch" and delivery.status == "Order Received":

        delivery.status = "Dispatched"
        delivery.dispatched_at = timezone.now()

    elif action == "arrive" and delivery.status == "Dispatched":

        # Software simulation only, not physical robot detection.
        delivery.status = "Arrived"
        delivery.arrived_at = timezone.now()

    elif action == "collect" and delivery.status == "Arrived":

        method = request.POST.get("verification_method")

        if method not in ["RFID", "PIN"]:
            messages.error(
                request,
                "Complete patient verification first."
            )
            return redirect("robot_dashboard")

        delivery.status = "Collected"
        delivery.verification_method = method
        delivery.collected_at = timezone.now()

    else:
        messages.error(
            request,
            "This delivery action is not valid at the current stage."
        )
        return redirect("robot_dashboard")

    delivery.save()

    messages.success(
        request,
        "Delivery status updated successfully."
    )

    return redirect("robot_dashboard")
