# Student Management System Pro

A production-grade full-stack Student Management System built using **Django 6**, **SQLite**, and **Bootstrap 5**, featuring Role-Based Access Control (RBAC), Bulk CSV Data Import with atomic rollback, ReportLab-powered PDF Transcripts, and interactive Chart.js Analytics.

---

## Production Features Overview

### 1. Role-Based Access Control (RBAC) & Custom Dashboards
- **Three Distinct User Roles**:
  - **Admin**: Full access to student CRUD operations, bulk CSV imports, system configuration, and aggregate analytics.
  - **Teacher**: Read/write access strictly to marks, grades, and daily attendance registers for assigned subjects/classes.
  - **Student**: Read-only access to personal profile, attendance records, semester marks, and instant transcript export.
- **Role-Based Redirects**: Automatic post-login routing directly to tailored role dashboards (`/` for Admin, `/teacher-dashboard/` for Teacher, `/student-dashboard/` for Student).
- **Role Decorators**: `@admin_required`, `@teacher_required`, and `@student_required` enforce view-level authorization.

### 2. Bulk Data Import (CSV) with Atomic Rollback
- Dedicated upload interface on the Admin console accepting `.csv` files.
- Parser validates required columns (`roll_number`, `first_name`, `last_name`, `email`, `department`).
- Enforces row-by-row validation for missing values, invalid email formats, and duplicate records.
- Powered by `transaction.atomic`: if any single row is corrupted or invalid, the entire transaction rolls back and clear row-specific error messages are displayed.
- One-click **Download Sample CSV** template available at `/sample-csv/`.

### 3. PDF Report Card & Transcript Generator
- Dynamic official transcript generation built with **ReportLab**.
- Downloadable for individual student profiles via `/student/<id>/report-card/`.
- Includes:
  - Official institutional header and title.
  - Student identity box (Full Name, Roll Number, Department, Enrollment Date).
  - Academic performance table (Subject Code, Name, Marks Obtained, Max Marks, Letter Grade, Remarks).
  - Attendance standing (Total lectures, Attended, Absent, Attendance Percentage with >=75% exam eligibility indicator).
  - Cumulative GPA / score summary and institutional seal/signature block.

### 4. Interactive Analytics Dashboard
- Computes real-time aggregate statistics:
  - Total students enrolled by department.
  - Department-wide attendance averages with 75% target threshold.
  - Academic grade distribution (A+, A, B, C, D, F) and institutional pass/fail rates.
  - Gender diversity demographics.
- Rendered using responsive **Chart.js** visualizations on both the Admin console and the dedicated `/analytics/` portal.

---

## Folder Structure

```text
it_project/
│
├── manage.py                          # Django management CLI
├── db.sqlite3                         # SQLite database (migrated & pre-seeded)
├── requirements.txt                   # Project dependencies (Django, reportlab)
├── README.md                          # Comprehensive documentation
│
├── student_management/                # Core project configuration
│   ├── settings.py                    # Settings, apps, auth, and message tags
│   ├── urls.py                        # Root URL routing
│   ├── wsgi.py                        # WSGI entry point
│   ├── asgi.py                        # ASGI entry point
│   └── __init__.py
│
└── students/                          # Core application
    ├── models.py                      # Student, UserProfile, Subject, Grade, Attendance
    ├── forms.py                       # StudentForm, CSVUploadForm, GradeForm, AttendanceForm
    ├── views.py                       # RBAC dashboards, CRUD, CSV import, PDF, Analytics
    ├── urls.py                        # Route definitions
    ├── decorators.py                  # RBAC permission decorators
    ├── analytics.py                   # Aggregation engine for Chart.js
    ├── csv_importer.py                # CSV parser with transaction.atomic
    ├── pdf_generator.py               # ReportLab PDF report card generator
    ├── admin.py                       # Model registration in Django admin
    ├── tests.py                       # 14 automated unit tests
    ├── apps.py                        # App configuration
    ├── migrations/                    # Database migrations
    ├── management/commands/           # Management commands
    │   └── seed_students.py           # Demo data seeder
    ├── static/students/css/           # Custom CSS styling
    │   └── style.css
    └── templates/students/            # Responsive HTML templates
        ├── base.html                  # Master layout, RBAC nav, Chart.js
        ├── login.html                 # Login page with quick-demo autofill
        ├── student_list.html          # Admin console, CSV modal & analytics preview
        ├── teacher_dashboard.html     # Teacher marks & attendance portal
        ├── student_dashboard.html     # Student profile, grades & PDF export
        ├── analytics.html             # Dedicated Interactive Analytics view
        ├── student_detail.html        # Comprehensive student profile
        ├── student_form.html          # Add / Edit student form
        └── student_confirm_delete.html# Safe deletion confirmation
```

---

## Demo Credentials (Pre-Configured)

| Role | Username | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full CRUD, Bulk CSV Import, System Analytics, Django Admin |
| **Teacher** | `teacher` | `teacher123` | Marks/Grades entry & Attendance register for assigned subjects |
| **Student** | `student` | `student123` | Personal profile view, Attendance records & PDF Report Card download |

*(The login screen also provides one-click autofill buttons for each role).*

---

## Quickstart Guide

1. Navigate to the project root:
   ```powershell
   cd c:\Users\kiezeal\Desktop\it_project
   ```

2. (Optional) Re-seed sample data anytime:
   ```powershell
   python manage.py seed_students
   ```

3. Start the development server:
   ```powershell
   python manage.py runserver
   ```

4. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Running Automated Tests

Run the full 14-test suite covering RBAC permissions, atomic CSV rollbacks, PDF generation, and analytics:
```powershell
python manage.py test
```
