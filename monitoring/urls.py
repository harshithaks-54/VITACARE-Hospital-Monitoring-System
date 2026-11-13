
from django.urls import path
from . import views

urlpatterns = [
    path("", views.monitoring_page, name="monitoring_page"),
    path("alerts/", views.alerts_page, name="alerts_page"),
]
