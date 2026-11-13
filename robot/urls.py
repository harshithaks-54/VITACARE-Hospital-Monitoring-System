
from django.urls import path
from . import views

urlpatterns = [
    path("", views.robot_dashboard, name="robot_dashboard"),

    path(
        "patient-details/<int:patient_id>/",
        views.patient_details,
        name="patient_details"
    ),

    path(
        "create/",
        views.create_delivery,
        name="create_delivery"
    ),

    path(
        "action/<int:delivery_id>/",
        views.delivery_action,
        name="delivery_action"
    ),
]
