
from django.urls import path

from . import views
from . import backup_views


urlpatterns = [
    # Main Settings page
    path("", views.settings_dashboard, name="settings_dashboard"),

    # Admin password
    path(
        "change-password/",
        views.change_admin_password,
        name="change_admin_password"
    ),

    # User Management
    path(
        "users/add/",
        views.add_user,
        name="add_user"
    ),
    path(
        "users/<int:user_id>/edit/",
        views.edit_user,
        name="edit_user"
    ),
    path(
        "users/<int:user_id>/toggle-status/",
        views.toggle_user_status,
        name="toggle_user_status"
    ),

    # Backup & Restore
    path(
        "backup/",
        backup_views.backup_dashboard,
        name="backup_dashboard"
    ),
    path(
        "backup/create/",
        backup_views.create_backup,
        name="create_backup"
    ),
    path(
        "backup/restore/",
        backup_views.restore_backup,
        name="restore_backup"
    ),
    path(
        "backup/download/<str:filename>/",
        backup_views.download_backup,
        name="download_backup"
    ),
    path(
        "backup/delete/<str:filename>/",
        backup_views.delete_backup,
        name="delete_backup"
    ),
]
