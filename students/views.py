from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, Http404
from django.db.models import Q
from django.utils import timezone

from .models import Student, UserProfile, Subject, Grade, Attendance
from .forms import StudentForm, CSVUploadForm, GradeForm, AttendanceForm
from .decorators import (
    get_user_role, get_dashboard_url_for_user,
    admin_required, teacher_required, student_required
)
from .pdf_generator import generate_report_card_pdf
from .csv_importer import parse_and_import_students_csv, generate_sample_csv
from .analytics import get_analytics_data


# ---------------------------------------------------------
# Authentication & Role-Based Redirection
# ---------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_url_for_user(request.user))

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            role = get_user_role(user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! Logged in as {role}.")

            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(get_dashboard_url_for_user(user))
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'students/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# ---------------------------------------------------------
# Feature 1: Role Dashboards
# ---------------------------------------------------------

@admin_required
def student_list(request):
    """Admin Dashboard: Student Directory, Quick Actions, and Analytics Preview."""
    query = request.GET.get('q', '').strip()
    selected_course = request.GET.get('course', '').strip()

    students = Student.objects.all()

    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(roll_number__icontains=query) |
            Q(email__icontains=query)
        )

    if selected_course:
        students = students.filter(course=selected_course)

    # Dashboard & Analytics Statistics
    courses = [choice[0] for choice in Student.COURSE_CHOICES]
    analytics = get_analytics_data()
    csv_form = CSVUploadForm()

    context = {
        'students': students,
        'query': query,
        'selected_course': selected_course,
        'courses': courses,
        'total_students': analytics['total_students'],
        'male_count': Student.objects.filter(gender='Male').count(),
        'female_count': Student.objects.filter(gender='Female').count(),
        'analytics': analytics,
        'csv_form': csv_form,
    }
    return render(request, 'students/student_list.html', context)


@teacher_required
def teacher_dashboard(request):
    """
    Teacher Dashboard:
    Read/write access only to marks/grades and attendance for assigned subjects/classes.
    """
    user = request.user
    # If superuser or Admin, show all subjects; otherwise show assigned subjects
    if user.is_superuser or get_user_role(user) == 'Admin':
        subjects = Subject.objects.all()
    else:
        subjects = Subject.objects.filter(teacher=user)

    selected_subject_id = request.GET.get('subject_id')
    active_subject = None
    if selected_subject_id:
        active_subject = subjects.filter(id=selected_subject_id).first()

    if not active_subject and subjects.exists():
        active_subject = subjects.first()

    # Students enrolled in this subject's department/course
    enrolled_students = []
    grades_for_subject = []
    recent_attendance = []

    if active_subject:
        enrolled_students = Student.objects.filter(course=active_subject.department)
        grades_for_subject = Grade.objects.filter(subject=active_subject).select_related('student')
        recent_attendance = Attendance.objects.filter(subject=active_subject).select_related('student')[:15]

    grade_form = GradeForm()
    attendance_form = AttendanceForm()

    context = {
        'subjects': subjects,
        'active_subject': active_subject,
        'enrolled_students': enrolled_students,
        'grades': grades_for_subject,
        'recent_attendance': recent_attendance,
        'grade_form': grade_form,
        'attendance_form': attendance_form,
        'today': timezone.now().date(),
    }
    return render(request, 'students/teacher_dashboard.html', context)


@student_required
def student_dashboard(request):
    """
    Student Dashboard:
    Read-only access to their personal profile, attendance records, and grades.
    """
    user = request.user
    # Locate student profile
    student = None
    if hasattr(user, 'profile') and user.profile.student:
        student = user.profile.student
    elif user.is_superuser:
        student = Student.objects.first()

    if not student:
        messages.warning(request, "No student profile is linked to your account. Please contact the administrator.")
        return render(request, 'students/student_dashboard.html', {'student': None})

    grades = student.grades.select_related('subject').all()
    attendance_summary = student.attendance_summary
    attendance_records = student.attendance_records.select_related('subject').all()[:20]

    context = {
        'student': student,
        'grades': grades,
        'attendance_summary': attendance_summary,
        'attendance_records': attendance_records,
    }
    return render(request, 'students/student_dashboard.html', context)


# ---------------------------------------------------------
# Teacher Actions: Marks & Attendance
# ---------------------------------------------------------

@teacher_required
def teacher_save_grade(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        marks_obtained = request.POST.get('marks_obtained')
        max_marks = request.POST.get('max_marks', '100')
        remarks = request.POST.get('remarks', '')

        try:
            student = get_object_or_404(Student, pk=student_id)
            subject = get_object_or_404(Subject, pk=subject_id)
            
            # Check teacher permission if not admin
            if not (request.user.is_superuser or get_user_role(request.user) == 'Admin'):
                if subject.teacher != request.user:
                    messages.error(request, "You can only enter grades for your assigned subjects.")
                    return redirect('teacher_dashboard')

            grade, created = Grade.objects.update_or_create(
                student=student,
                subject=subject,
                defaults={
                    'marks_obtained': float(marks_obtained),
                    'max_marks': float(max_marks),
                    'remarks': remarks,
                    'grade_letter': '',  # Will auto-calculate on save
                }
            )
            action_text = "recorded" if created else "updated"
            messages.success(request, f"Grade {action_text} successfully for {student.full_name} ({subject.code}): {grade.grade_letter}")
        except Exception as e:
            messages.error(request, f"Failed to save grade: {str(e)}")

        return redirect(f"/teacher-dashboard/?subject_id={subject_id}")
    return redirect('teacher_dashboard')


@teacher_required
def teacher_save_attendance(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        att_date = request.POST.get('date') or timezone.now().date()
        subject = get_object_or_404(Subject, pk=subject_id)

        # Check teacher permission
        if not (request.user.is_superuser or get_user_role(request.user) == 'Admin'):
            if subject.teacher != request.user:
                messages.error(request, "You can only record attendance for your assigned subjects.")
                return redirect('teacher_dashboard')

        # Batch attendance update: status_<student_id>
        updated_count = 0
        students = Student.objects.filter(course=subject.department)
        for st in students:
            param_name = f"status_{st.pk}"
            status = request.POST.get(param_name)
            if status:
                Attendance.objects.update_or_create(
                    student=st,
                    subject=subject,
                    date=att_date,
                    defaults={'status': status}
                )
                updated_count += 1

        messages.success(request, f"Attendance marked for {updated_count} students on {att_date} for {subject.code}.")
        return redirect(f"/teacher-dashboard/?subject_id={subject_id}")
    return redirect('teacher_dashboard')


# ---------------------------------------------------------
# Feature 2: Bulk CSV Import & Sample Download
# ---------------------------------------------------------

@admin_required
def import_students_csv_view(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            success, count, errors = parse_and_import_students_csv(csv_file)
            if success:
                messages.success(request, f"Successfully imported {count} student records with atomic transaction verification!")
            else:
                error_html = "<br/>".join(errors[:8])
                if len(errors) > 8:
                    error_html += f"<br/>...and {len(errors) - 8} more errors. Entire transaction was rolled back."
                messages.error(request, f"<strong>Bulk Import Failed (Rolled Back):</strong><br/>{error_html}")
        else:
            messages.error(request, "Invalid file upload. Please ensure you select a valid .csv file under 5MB.")

    return redirect('student_list')


def download_sample_csv_view(request):
    csv_content = generate_sample_csv()
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_students_import.csv"'
    return response


# ---------------------------------------------------------
# Feature 3: PDF Report Card / Transcript Generator
# ---------------------------------------------------------

def export_report_card_pdf_view(request, pk):
    """
    Exports clean, official PDF Report Card / Transcript for a student.
    Enforces RBAC: Admin and Teacher can access any student; Student can only access their own.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to download report cards.")
        return redirect('login')

    student = get_object_or_404(Student, pk=pk)
    user_role = get_user_role(request.user)

    # Permission check for Student role
    if user_role == 'Student' and not request.user.is_superuser:
        user_student = getattr(request.user.profile, 'student', None)
        if not user_student or user_student.pk != student.pk:
            messages.error(request, "Permission Denied: You may only access your own academic report card.")
            return redirect('student_dashboard')

    pdf_buffer = generate_report_card_pdf(student)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    filename = f"ReportCard_{student.roll_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ---------------------------------------------------------
# Feature 4: Interactive Analytics Dashboard
# ---------------------------------------------------------

@admin_required
def analytics_dashboard(request):
    """Dedicated Interactive Analytics Dashboard with Chart.js."""
    analytics = get_analytics_data()
    return render(request, 'students/analytics.html', {'analytics': analytics})


# ---------------------------------------------------------
# Student CRUD Operations
# ---------------------------------------------------------

def student_detail(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')

    student = get_object_or_404(Student, pk=pk)
    user_role = get_user_role(request.user)

    # If student role, ensure they can only view their own profile
    if user_role == 'Student' and not request.user.is_superuser:
        user_student = getattr(request.user.profile, 'student', None)
        if not user_student or user_student.pk != student.pk:
            messages.error(request, "You can only view your own profile.")
            return redirect('student_dashboard')

    grades = student.grades.select_related('subject').all()
    attendance_summary = student.attendance_summary
    attendance_records = student.attendance_records.select_related('subject').all()[:15]

    return render(request, 'students/student_detail.html', {
        'student': student,
        'grades': grades,
        'attendance_summary': attendance_summary,
        'attendance_records': attendance_records,
        'user_role': user_role,
    })


@admin_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student "{student.full_name}" has been added successfully!')
            return redirect('student_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm()

    return render(request, 'students/student_form.html', {
        'form': form,
        'title': 'Add New Student',
        'button_text': 'Save Student',
    })


@admin_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save()
            messages.success(request, f'Student "{student.full_name}" has been updated successfully!')
            return redirect('student_detail', pk=student.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {
        'form': form,
        'student': student,
        'title': f'Edit Student: {student.full_name}',
        'button_text': 'Update Student',
    })


@admin_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'Student "{name}" has been deleted successfully.')
        return redirect('student_list')

    return render(request, 'students/student_confirm_delete.html', {'student': student})
