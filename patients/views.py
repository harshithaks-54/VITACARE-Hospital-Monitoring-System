
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum

from .models import Patient, Room
from .forms import PatientForm
from .room_forms import RoomForm


# ==========================================
# ROOM CAPACITY VALIDATION
# ==========================================

def check_room_capacity(form, patient=None):
    """
    Check whether a room has space for another admitted patient.
    Returns an error message if the room is full.
    """

    room = form.cleaned_data.get("room")
    status = form.cleaned_data.get("status")

    # No room assigned or patient is not admitted
    if not room or status != "Admitted":
        return None

    # Lock the selected room during the capacity check
    locked_room = Room.objects.select_for_update().get(pk=room.pk)

    admitted_patients = Patient.objects.filter(
        room=locked_room,
        status="Admitted"
    )

    # Do not count the current patient while editing
    if patient:
        admitted_patients = admitted_patients.exclude(
            pk=patient.pk
        )

    occupied_beds = admitted_patients.count()

    if occupied_beds >= locked_room.bed_capacity:
        return (
            f"Room {locked_room.room_number} is full. "
            f"Bed capacity: {locked_room.bed_capacity}, "
            f"Occupied beds: {occupied_beds}. "
            "Please select another room."
        )

    return None


# ==========================================
# PATIENT MANAGEMENT
# ==========================================

# Display all patients and search patients
def patient_list(request):

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    patients = (
        Patient.objects
        .select_related("room")
        .all()
        .order_by("-admission_date")
    )

    if status_filter == "Admitted":
        patients = patients.filter(status="Admitted")

    if search_query:
        patients = patients.filter(
            Q(patient_id__icontains=search_query) |
            Q(name__icontains=search_query)
        )

    context = {
        "patients": patients,
        "search_query": search_query,
        "total_patients": Patient.objects.count(),
        "admitted_patients": Patient.objects.filter(
            status="Admitted"
        ).count(),
    }

    return render(request, "patients.html", context)


# Add new patient
def add_patient(request):

    if request.method == "POST":

        form = PatientForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                capacity_error = check_room_capacity(form)

                if capacity_error:
                    messages.error(request, capacity_error)

                    return render(
                        request,
                        "add_patient.html",
                        {"form": form}
                    )

                form.save()

            messages.success(
                request,
                "Patient added successfully!"
            )

            return redirect("patient_list")

    else:
        form = PatientForm()

    return render(
        request,
        "add_patient.html",
        {"form": form}
    )


# View patient details
def patient_detail(request, pk):

    patient = get_object_or_404(
        Patient.objects.select_related("room"),
        pk=pk
    )

    return render(
        request,
        "patient_detail.html",
        {"patient": patient}
    )


# Edit patient
def edit_patient(request, pk):

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            instance=patient
        )

        if form.is_valid():

            with transaction.atomic():

                capacity_error = check_room_capacity(
                    form,
                    patient=patient
                )

                if capacity_error:
                    messages.error(request, capacity_error)

                    return render(
                        request,
                        "edit_patient.html",
                        {
                            "form": form,
                            "patient": patient
                        }
                    )

                form.save()

            messages.success(
                request,
                "Patient details updated successfully!"
            )

            return redirect("patient_list")

    else:
        form = PatientForm(instance=patient)

    return render(
        request,
        "edit_patient.html",
        {
            "form": form,
            "patient": patient
        }
    )


# Delete patient
def delete_patient(request, pk):

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == "POST":

        patient_name = patient.name
        patient.delete()

        messages.success(
            request,
            f"{patient_name} has been deleted successfully!"
        )

        return redirect("patient_list")

    # Prevent opening a separate delete page
    return redirect("patient_list")


# ==========================================
# ROOM MANAGEMENT
# ==========================================

# Display rooms, search rooms and calculate occupancy
def room_list(request):

    search_query = request.GET.get("q", "").strip()
    available_filter = request.GET.get("available", "").strip()

    rooms = (
        Room.objects
        .all()
        .order_by("room_number")
    )

    if search_query:
        rooms = rooms.filter(
            Q(room_number__icontains=search_query)
        )

    room_data = []

    # Calculate actual bed occupancy for each room
    for room in rooms:

        occupied_beds = room.patients.filter(
            status="Admitted"
        ).count()

        available_beds = max(
            room.bed_capacity - occupied_beds,
            0
        )

        occupancy = (
            round(
                (occupied_beds / room.bed_capacity) * 100
            )
            if room.bed_capacity > 0
            else 0
        )

        is_full = occupied_beds >= room.bed_capacity

        # Show only rooms with available beds when filter is selected
        if available_filter == "1" and available_beds <= 0:
            continue

        room_data.append({
            "room": room,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "occupancy": occupancy,
            "is_full": is_full,
        })

    # Overall room and bed statistics
    total_rooms = Room.objects.count()

    total_beds = (
        Room.objects.aggregate(
            total=Sum("bed_capacity")
        )["total"] or 0
    )

    occupied_beds = Patient.objects.filter(
        status="Admitted",
        room__isnull=False
    ).count()

    available_beds = max(
        total_beds - occupied_beds,
        0
    )

    # Count rooms that have at least one available bed
    available_rooms = 0

    for room in Room.objects.all():

        admitted_count = room.patients.filter(
            status="Admitted"
        ).count()

        if admitted_count < room.bed_capacity:
            available_rooms += 1

    context = {
        "room_data": room_data,
        "search_query": search_query,
        "total_rooms": total_rooms,
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "available_rooms": available_rooms,
    }

    return render(
        request,
        "rooms.html",
        context
    )


# Add room
def add_room(request):

    if request.method == "POST":

        form = RoomForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Room added successfully!"
            )

            return redirect("room_list")

    else:
        form = RoomForm()

    return render(
        request,
        "room_form.html",
        {
            "form": form,
            "page_title": "Add New Room",
            "button_text": "Save Room",
        }
    )


# Edit room
def edit_room(request, pk):

    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":

        with transaction.atomic():

            # Lock the room before updating its capacity
            locked_room = Room.objects.select_for_update().get(
                pk=pk
            )

            form = RoomForm(
                request.POST,
                instance=locked_room
            )

            if form.is_valid():

                new_capacity = form.cleaned_data.get(
                    "bed_capacity"
                )

                admitted_count = Patient.objects.filter(
                    room=locked_room,
                    status="Admitted"
                ).count()

                if new_capacity < admitted_count:

                    messages.error(
                        request,
                        f"Cannot reduce capacity to {new_capacity}. "
                        f"This room already has {admitted_count} "
                        "admitted patients."
                    )

                    return render(
                        request,
                        "room_form.html",
                        {
                            "form": form,
                            "room": locked_room,
                            "page_title": "Edit Room",
                            "button_text": "Update Room",
                        }
                    )

                form.save()

                messages.success(
                    request,
                    "Room updated successfully!"
                )

                return redirect("room_list")

    else:

        form = RoomForm(instance=room)

    return render(
        request,
        "room_form.html",
        {
            "form": form,
            "room": room,
            "page_title": "Edit Room",
            "button_text": "Update Room",
        }
    )


# Delete room
def delete_room(request, pk):

    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":

        # Prevent deleting a room with admitted patients
        if room.patients.filter(status="Admitted").exists():

            messages.error(
                request,
                "This room has admitted patients. "
                "Move or discharge them before deleting the room."
            )

            return redirect("room_list")

        room.delete()

        messages.success(
            request,
            "Room deleted successfully!"
        )

        return redirect("room_list")

    return render(
        request,
        "delete_room.html",
        {
            "room": room,
        }
    )
