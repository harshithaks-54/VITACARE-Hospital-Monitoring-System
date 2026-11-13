
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import AdminProfile, HospitalDetails
from .forms import (
    AdminProfileForm,
    UserManagementForm,
    HospitalDetailsForm,
)


# --------------------------------------------------
# SETTINGS CONFIGURATION
# --------------------------------------------------

SETTINGS_SECTIONS = {
    "profile": "Admin Profile",
    "users": "User Management",
    "hospital": "Hospital Details",
    "preferences": "System Preferences",
    "about": "About System",
}


# --------------------------------------------------
# COMMON REDIRECT FUNCTION
# --------------------------------------------------

def redirect_to_settings(section="profile"):
    url = reverse("settings_dashboard")
    return redirect(f"{url}?section={section}")


# --------------------------------------------------
# PERMISSION FUNCTIONS
# --------------------------------------------------

def can_manage_users(user):
    if not user.is_authenticated:
        return False

    return (
        user.is_superuser
        or user.groups.filter(name="Admin").exists()
    )


def get_user_role(user):
    if user.is_superuser:
        return "Admin"

    group = user.groups.first()

    if group:
        return group.name

    return "Not assigned"


def assign_user_role(user, role):
    allowed_roles = ["Admin", "Doctor", "Nurse", "Pharmacist"]

    if role not in allowed_roles:
        return

    group, created = Group.objects.get_or_create(name=role)

    user.groups.set([group])

    if role == "Admin":
        user.is_staff = True
    else:
        user.is_staff = False

    user.save()


# --------------------------------------------------
# MAIN SETTINGS DASHBOARD
# --------------------------------------------------

@login_required
def settings_dashboard(request):

    # Get the selected settings section.
    selected_section = request.GET.get("section", "profile")

    if selected_section not in SETTINGS_SECTIONS:
        selected_section = "profile"

    # Get or create admin profile.
    profile, created = AdminProfile.objects.get_or_create(
        user=request.user
    )

    # Get or create hospital details.
    hospital = HospitalDetails.objects.first()

    if hospital is None:
        hospital = HospitalDetails.objects.create(
            hospital_name="VITACARE Hospital"
        )

    # --------------------------------------------------
    # ADMIN PROFILE FORM
    # --------------------------------------------------

    if request.method == "POST" and selected_section == "profile":

        form = AdminProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():

            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()

            full_name = form.cleaned_data.get(
                "full_name", ""
            ).strip()

            name_parts = full_name.split(maxsplit=1)

            request.user.first_name = (
                name_parts[0] if name_parts else ""
            )

            request.user.last_name = (
                name_parts[1] if len(name_parts) > 1 else ""
            )

            request.user.email = form.cleaned_data.get(
                "email", ""
            )

            request.user.save()

            messages.success(
                request,
                "Admin profile updated successfully."
            )

            return redirect_to_settings("profile")

        else:
            messages.error(
                request,
                "Please correct the errors in the profile form."
            )

    else:

        form = AdminProfileForm(
            instance=profile,
            initial={
                "full_name": request.user.get_full_name(),
                "email": request.user.email,
            }
        )

    # --------------------------------------------------
    # HOSPITAL DETAILS FORM
    # --------------------------------------------------

    if request.method == "POST" and selected_section == "hospital":

        hospital_form = HospitalDetailsForm(
            request.POST,
            instance=hospital
        )

        if hospital_form.is_valid():

            hospital_form.save()

            messages.success(
                request,
                "Hospital details updated successfully."
            )

            return redirect_to_settings("hospital")

        else:
            messages.error(
                request,
                "Please correct the errors in hospital details."
            )

    else:

        hospital_form = HospitalDetailsForm(
            instance=hospital
        )

    # --------------------------------------------------
    # USER MANAGEMENT
    # --------------------------------------------------

    staff_users = User.objects.all().order_by("username")

    search = request.GET.get("search", "").strip()

    if search:
        staff_users = staff_users.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    # --------------------------------------------------
    # CONTEXT
    # --------------------------------------------------

    context = {
        "selected_section": selected_section,
        "section_title": SETTINGS_SECTIONS[selected_section],

        "admin_user": request.user,
        "profile": profile,
        "form": form,

        "hospital": hospital,
        "hospital_form": hospital_form,

        "staff_users": staff_users,
        "search": search,

        "can_manage_users": can_manage_users(request.user),
        "is_super_admin": request.user.is_superuser,
    }

    return render(
        request,
        "system_settings/settings.html",
        context
    )


# --------------------------------------------------
# ADD USER
# --------------------------------------------------

@login_required
def add_user(request):

    if not can_manage_users(request.user):
        raise PermissionDenied

    if request.method == "POST":

        form = UserManagementForm(request.POST)

        if form.is_valid():

            new_user = form.save(commit=False)

            password = form.cleaned_data["password"]
            new_user.set_password(password)

            new_user.save()

            role = form.cleaned_data["role"]
            assign_user_role(new_user, role)

            messages.success(
                request,
                "New user added successfully."
            )

            return redirect_to_settings("users")

        else:
            messages.error(
                request,
                "Please correct the errors in the user form."
            )

    else:
        form = UserManagementForm()

    return render(
        request,
        "system_settings/user_form.html",
        {
            "form": form,
            "page_title": "Add New User",
            "button_text": "Add User",
        }
    )


# --------------------------------------------------
# EDIT USER
# --------------------------------------------------

@login_required
def edit_user(request, user_id):

    if not can_manage_users(request.user):
        raise PermissionDenied

    selected_user = get_object_or_404(
        User,
        id=user_id
    )

    if request.method == "POST":

        form = UserManagementForm(
            request.POST,
            instance=selected_user
        )

        if form.is_valid():

            edited_user = form.save(commit=False)

            password = form.cleaned_data.get("password")

            if password:
                edited_user.set_password(password)

            edited_user.save()

            role = form.cleaned_data["role"]
            assign_user_role(edited_user, role)

            messages.success(
                request,
                "User details updated successfully."
            )

            return redirect_to_settings("users")

        else:
            messages.error(
                request,
                "Please correct the errors in the user form."
            )

    else:

        form = UserManagementForm(
            instance=selected_user,
            initial={
                "role": get_user_role(selected_user)
            }
        )

    return render(
        request,
        "system_settings/user_form.html",
        {
            "form": form,
            "selected_user": selected_user,
            "page_title": "Edit User",
            "button_text": "Update User",
        }
    )


# --------------------------------------------------
# ACTIVATE / DEACTIVATE USER
# --------------------------------------------------

@login_required
@require_POST
def toggle_user_status(request, user_id):

    if not can_manage_users(request.user):
        raise PermissionDenied

    selected_user = get_object_or_404(
        User,
        id=user_id
    )

    if selected_user.id == request.user.id:

        messages.error(
            request,
            "You cannot deactivate your own account."
        )

        return redirect_to_settings("users")

    selected_user.is_active = not selected_user.is_active
    selected_user.save()

    if selected_user.is_active:

        messages.success(
            request,
            f"{selected_user.username} has been activated."
        )

    else:

        messages.success(
            request,
            f"{selected_user.username} has been deactivated."
        )

    return redirect_to_settings("users")


# --------------------------------------------------
# CHANGE ADMIN PASSWORD
# --------------------------------------------------

@login_required
def change_admin_password(request):

    if request.method == "POST":

        password_form = PasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if password_form.is_valid():

            updated_user = password_form.save()

            update_session_auth_hash(
                request,
                updated_user
            )

            messages.success(
                request,
                "Password changed successfully."
            )

            return redirect_to_settings("profile")

        else:

            messages.error(
                request,
                "Please correct the password errors."
            )

    else:

        password_form = PasswordChangeForm(
            user=request.user
        )

    return render(
        request,
        "system_settings/change_password.html",
        {
            "password_form": password_form,
        }
    )
