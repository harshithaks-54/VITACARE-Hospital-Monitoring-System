
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST


BACKUP_DIR = os.path.join(settings.BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def get_mysql_config():
    """Read the database connection settings from Django."""
    database = settings.DATABASES["default"]

    if database.get("ENGINE") != "django.db.backends.mysql":
        raise RuntimeError("VITACARE is not configured to use MySQL.")

    return {
        "name": str(database["NAME"]),
        "user": str(database.get("USER", "")),
        "password": str(database.get("PASSWORD", "")),
        "host": str(database.get("HOST") or "localhost"),
        "port": str(database.get("PORT") or "3306"),
    }


def get_mysql_environment(config):
    """Pass the MySQL password through the process environment."""
    env = os.environ.copy()
    env["MYSQL_PWD"] = config["password"]
    return env


def get_backup_path(filename):
    """Prevent directory traversal and only allow ZIP backup files."""
    if not filename or filename != os.path.basename(filename):
        raise Http404("Backup file not found.")

    if not filename.lower().endswith(".zip"):
        raise Http404("Invalid backup file.")

    path = os.path.join(BACKUP_DIR, filename)

    if not os.path.isfile(path):
        raise Http404("Backup file not found.")

    return path


def list_backups():
    """Return the saved ZIP backups, newest first."""
    backups = []

    for filename in os.listdir(BACKUP_DIR):
        if not filename.lower().endswith(".zip"):
            continue

        path = os.path.join(BACKUP_DIR, filename)

        if not os.path.isfile(path):
            continue

        created = datetime.fromtimestamp(
            os.path.getmtime(path),
            tz=timezone.get_current_timezone()
        )

        size_mb = os.path.getsize(path) / (1024 * 1024)

        backups.append({
            "name": filename,
            "created_at": created,
            "size_mb": round(size_mb, 2),
        })

    backups.sort(key=lambda item: item["created_at"], reverse=True)
    return backups


@login_required
def backup_dashboard(request):
    """Display the Backup & Restore page."""
    return render(
        request,
        "system_settings/backup_restore.html",
        {
            "backups": list_backups(),
            "admin_user": request.user,
        }
    )


@login_required
@require_POST
def create_backup(request):
    """Create a ZIP containing a MySQL database dump and media files."""
    config = get_mysql_config()

    mysqldump = shutil.which("mysqldump")

    if not mysqldump:
        messages.error(
            request,
            "mysqldump was not found. Add the MySQL Server bin folder to Windows PATH."
        )
        return redirect("backup_dashboard")

    timestamp = timezone.localtime().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"vitacare_backup_{timestamp}.zip"
    zip_path = os.path.join(BACKUP_DIR, filename)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_path = os.path.join(temp_dir, "database.sql")

            command = [
                mysqldump,
                "--host", config["host"],
                "--port", config["port"],
                "--user", config["user"],
                "--default-character-set=utf8mb4",
                "--single-transaction",
                "--routines",
                "--triggers",
                config["name"],
            ]

            with open(sql_path, "wb") as sql_file:
                result = subprocess.run(
                    command,
                    stdout=sql_file,
                    stderr=subprocess.PIPE,
                    env=get_mysql_environment(config),
                    check=False,
                )

            if result.returncode != 0:
                error = result.stderr.decode("utf-8", errors="replace")
                raise RuntimeError(error or "MySQL backup command failed.")

            if os.path.getsize(sql_path) == 0:
                raise RuntimeError("The database backup file is empty.")

            with zipfile.ZipFile(
                zip_path, "w", compression=zipfile.ZIP_DEFLATED
            ) as archive:
                archive.write(sql_path, arcname="database.sql")

                archive.writestr(
                    "backup_info.txt",
                    (
                        "VITACARE Database Backup\n"
                        f"Database: {config['name']}\n"
                        f"Created: {timezone.localtime().isoformat()}\n"
                    )
                )

                media_root = getattr(settings, "MEDIA_ROOT", None)

                if media_root and os.path.isdir(media_root):
                    for root, _, files in os.walk(media_root):
                        for file in files:
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(
                                full_path, settings.BASE_DIR
                            )

                            archive.write(
                                full_path,
                                arcname=relative_path.replace("\\", "/")
                            )

        messages.success(
            request,
            f"Backup created successfully: {filename}"
        )

    except Exception as error:
        if os.path.exists(zip_path):
            os.remove(zip_path)

        messages.error(request, f"Backup failed: {error}")

    return redirect("backup_dashboard")


@login_required
@require_POST
def restore_backup(request):
    """
    Restore the MySQL database from an uploaded VITACARE ZIP backup.
    This replaces database tables/data from the selected dump.
    """
    uploaded_file = request.FILES.get("backup_file")

    if not uploaded_file:
        messages.error(request, "Please select a backup ZIP file.")
        return redirect("backup_dashboard")

    if not uploaded_file.name.lower().endswith(".zip"):
        messages.error(request, "Only ZIP backup files are accepted.")
        return redirect("backup_dashboard")

    config = get_mysql_config()
    mysql_client = shutil.which("mysql")

    if not mysql_client:
        messages.error(
            request,
            "The MySQL command-line client was not found. Add the MySQL Server bin folder to Windows PATH."
        )
        return redirect("backup_dashboard")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "uploaded_backup.zip")

            with open(zip_path, "wb") as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as archive:
                names = archive.namelist()

                if "database.sql" not in names:
                    raise RuntimeError(
                        "This ZIP does not contain a VITACARE database.sql backup."
                    )

                # Extract the SQL dump to a temporary location.
                sql_path = os.path.join(temp_dir, "database.sql")

                with archive.open("database.sql") as source:
                    with open(sql_path, "wb") as destination:
                        shutil.copyfileobj(source, destination)

                if os.path.getsize(sql_path) == 0:
                    raise RuntimeError("The database backup is empty.")

                command = [
                    mysql_client,
                    "--host", config["host"],
                    "--port", config["port"],
                    "--user", config["user"],
                    "--default-character-set=utf8mb4",
                    config["name"],
                ]

                with open(sql_path, "rb") as sql_file:
                    result = subprocess.run(
                        command,
                        stdin=sql_file,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=get_mysql_environment(config),
                        check=False,
                    )

                if result.returncode != 0:
                    error = result.stderr.decode("utf-8", errors="replace")
                    raise RuntimeError(error or "MySQL restore command failed.")

                # Restore media files only from the media/ folder.
                media_root = getattr(settings, "MEDIA_ROOT", None)

                if media_root:
                    for member in names:
                        normalized = member.replace("\\", "/")

                        if not normalized.startswith("media/"):
                            continue

                        if normalized.startswith("/") or ".." in normalized.split("/"):
                            raise RuntimeError("Unsafe file path found in backup.")

                        target_path = os.path.realpath(
                            os.path.join(settings.BASE_DIR, normalized)
                        )
                        allowed_root = os.path.realpath(settings.BASE_DIR)

                        if not target_path.startswith(allowed_root + os.sep):
                            raise RuntimeError("Unsafe media file path in backup.")

                        if member.endswith("/"):
                            os.makedirs(target_path, exist_ok=True)
                            continue

                        os.makedirs(os.path.dirname(target_path), exist_ok=True)

                        with archive.open(member) as source:
                            with open(target_path, "wb") as destination:
                                shutil.copyfileobj(source, destination)

        messages.success(
            request,
            "Database restore completed successfully. Please verify the restored records."
        )

    except zipfile.BadZipFile:
        messages.error(request, "The selected file is not a valid ZIP archive.")

    except Exception as error:
        messages.error(request, f"Restore failed: {error}")

    return redirect("backup_dashboard")


@login_required
def download_backup(request, filename):
    """Download a saved backup ZIP file."""
    path = get_backup_path(filename)

    return FileResponse(
        open(path, "rb"),
        as_attachment=True,
        filename=filename
    )


@login_required
@require_POST
def delete_backup(request, filename):
    """Delete a saved backup ZIP file."""
    try:
        path = get_backup_path(filename)
        os.remove(path)
        messages.success(request, "Backup deleted successfully.")

    except Http404:
        messages.error(request, "Backup file not found.")

    except Exception as error:
        messages.error(request, f"Could not delete backup: {error}")

    return redirect("backup_dashboard")
