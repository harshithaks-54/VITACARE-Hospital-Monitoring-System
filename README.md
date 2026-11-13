# VITACARE – Intelligent Centralized Hospital Monitoring System

## Project Overview
VITACARE is an intelligent hospital monitoring system designed to simplify and improve hospital management through centralized monitoring and automation.

The system provides a unified platform to manage patient information, hospital rooms, vital signs, alerts, medicines, and medicine delivery operations.

## Key Features

- **Dashboard:** Displays an overview of hospital activities and patient statistics.
- **Patient Management:** Maintains patient records and details.
- **Room Management:** Manages room availability and patient allocation.
- **Patient Monitoring:** Displays patient vital readings such as heart rate, blood pressure, temperature, and SpO₂.
- **Alerts & Notifications:** Helps identify patients who require attention.
- **Medicine Management:** Maintains medicine-related information.
- **Delivery Robot:** Provides a dedicated interface for medicine delivery operations.
- **Reports & Analytics:** Presents hospital monitoring information and reports.
- **Settings & Admin Profile:** Provides administrative settings and profile management.

## Technologies Used

- Python
- Django
- MySQL
- HTML
- CSS
- JavaScript
- IoT Technology (ESP32 and sensors)

## Project Structure

```text
VITACARE/
│
├── dashboard/
├── patients/
├── monitoring/
├── medicines/
├── robot/
├── reports/
├── system_settings/
├── templates/
├── static/
├── vitacare/
├── manage.py
└── README.md
```

## Installation and Setup

1. Clone the repository:

   ```bash
   git clone YOUR_GITHUB_REPOSITORY_URL
   ```

2. Navigate to the project directory:

   ```bash
   cd vitacare
   ```

3. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate
   ```

4. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure your MySQL database and Django environment variables in your local environment.

6. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

7. Start the development server:

   ```bash
   python manage.py runserver
   ```

8. Open the application in your browser:

   `http://127.0.0.1:8000/`

## Note
This project was developed as an academic project. Hardware-dependent features may require the corresponding ESP32 devices and sensors for real-time operation.