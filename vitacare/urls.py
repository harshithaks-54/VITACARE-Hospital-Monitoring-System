
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path("patients/", include("patients.urls")),
    path("monitoring/", include("monitoring.urls")),
        path("robot/", include("robot.urls")),
        path("reports/", include("reports.urls")),
        path("settings/", include("system_settings.urls")),
]
