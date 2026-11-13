
from django.urls import path
from . import views

urlpatterns = [
    path("", views.patient_list, name="patient_list"),
    path("add/", views.add_patient, name="add_patient"),
    path("<int:pk>/", views.patient_detail, name="patient_detail"),
    path("<int:pk>/edit/", views.edit_patient, name="edit_patient"),
    path("<int:pk>/delete/", views.delete_patient, name="delete_patient"),
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/add/", views.add_room, name="add_room"),
    path("rooms/<int:pk>/edit/", views.edit_room, name="edit_room"),
    path("rooms/<int:pk>/delete/", views.delete_room, name="delete_room"),
]
