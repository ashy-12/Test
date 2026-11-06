import io
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Student, UserProfile, Subject, Grade, Attendance
from .analytics import get_analytics_data
from .pdf_generator import generate_report_card_pdf


class StudentModelTest(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            roll_number="CS-101",
            email="john.doe@example.com",
            phone="+1234567890",
            gender="Male",
            course="Computer Science",
            date_of_birth=date(2002, 5, 10),
            enrollment_date=date(2023, 8, 1),
            address="123 Main St",
        )
        self.subject = Subject.objects.create(
            name="Data Structures",
            code="CS-201",
            department="Computer Science"
        )
        Grade.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=90.0,
            max_marks=100.0,
        )
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date(2024, 1, 10),
            status="Present"
        )
        Attendance.objects.create(
            student=self.student,
            subject=self.subject,
            date=date(2024, 1, 11),
            status="Absent"
        )

    def test_student_str(self):
        self.assertEqual(str(self.student), "John Doe (CS-101)")

    def test_student_full_name(self):
        self.assertEqual(self.student.full_name, "John Doe")

    def test_cumulative_attendance(self):
        # 1 Present out of 2 total = 50.0%
        self.assertEqual(self.student.cumulative_attendance_percentage, 50.0)

    def test_average_marks(self):
        self.assertEqual(self.student.average_marks, 90.0)


class RBACTest(TestCase):
    def setUp(self):
        # Admin User
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='password123'
        )
        UserProfile.objects.update_or_create(user=self.admin_user, defaults={'role': 'Admin'})

        # Student Model & User
        self.student = Student.objects.create(
            first_name="Alice",
            last_name="Student",
            roll_number="CS-001",
            email="alice@test.com",
            course="Computer Science",
            gender="Female"
        )
        self.student_user = User.objects.create_user(
            username='test_student',
            email='alice@test.com',
            password='password123'
        )
        UserProfile.objects.update_or_create(
            user=self.student_user,
            defaults={'role': 'Student', 'student': self.student}
        )

        # Teacher User
        self.teacher_user = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='password123'
        )
        UserProfile.objects.update_or_create(user=self.teacher_user, defaults={'role': 'Teacher'})

        self.subject = Subject.objects.create(
            name="Databases",
            code="CS-301",
            department="Computer Science",
            teacher=self.teacher_user
        )

    def test_admin_access(self):
        self.client.login(username='test_admin', password='password123')
        response = self.client.get(reverse('student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Management Console")

    def test_teacher_access(self):
        self.client.login(username='test_teacher', password='password123')
        # Teacher accessing teacher dashboard
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teacher Academic Portal")

        # Teacher blocked from admin create view
        create_resp = self.client.get(reverse('student_create'))
        self.assertRedirects(create_resp, reverse('teacher_dashboard'))

    def test_student_access(self):
        self.client.login(username='test_student', password='password123')
        # Student accessing student dashboard
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Student")

        # Student blocked from admin list view
        list_resp = self.client.get(reverse('student_list'))
        self.assertRedirects(list_resp, reverse('student_dashboard'))

    def test_login_redirection_by_role(self):
        # Teacher login redirects to teacher dashboard
        resp = self.client.post(reverse('login'), {'username': 'test_teacher', 'password': 'password123'})
        self.assertRedirects(resp, reverse('teacher_dashboard'))


class CSVImportTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='csv_admin', password='password123')
        UserProfile.objects.update_or_create(user=self.admin, defaults={'role': 'Admin'})
        self.client.login(username='csv_admin', password='password123')

    def test_valid_csv_import(self):
        csv_data = (
            "roll_number,first_name,last_name,email,department,gender\n"
            "CS-999,Bulk,One,bulk.one@example.com,Computer Science,Male\n"
            "CS-998,Bulk,Two,bulk.two@example.com,Computer Science,Female\n"
        )
        csv_file = SimpleUploadedFile("students.csv", csv_data.encode('utf-8'), content_type="text/csv")
        response = self.client.post(reverse('import_csv'), {'csv_file': csv_file})
        self.assertRedirects(response, reverse('student_list'))
        self.assertTrue(Student.objects.filter(roll_number='CS-999').exists())
        self.assertTrue(Student.objects.filter(roll_number='CS-998').exists())

    def test_corrupted_csv_atomic_rollback(self):
        # Row 1 is valid, but Row 2 has an invalid email and Row 3 has a duplicate roll number
        csv_data = (
            "roll_number,first_name,last_name,email,department\n"
            "CS-888,Valid,Student,valid.student@example.com,Computer Science\n"
            "CS-889,Corrupt,User,not-an-email,Computer Science\n"
            "CS-888,Duplicate,User,dup@example.com,Computer Science\n"
        )
        csv_file = SimpleUploadedFile("corrupted.csv", csv_data.encode('utf-8'), content_type="text/csv")
        response = self.client.post(reverse('import_csv'), {'csv_file': csv_file}, follow=True)
        self.assertContains(response, "Bulk Import Failed (Rolled Back)")
        # Atomic rollback verification: Even the first valid row MUST NOT exist in DB
        self.assertFalse(Student.objects.filter(roll_number='CS-888').exists())
        self.assertFalse(Student.objects.filter(roll_number='CS-889').exists())


class PDFReportCardTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='pdf_admin', password='password123')
        UserProfile.objects.update_or_create(user=self.admin, defaults={'role': 'Admin'})
        self.client.login(username='pdf_admin', password='password123')

        self.student = Student.objects.create(
            first_name="Report",
            last_name="Tester",
            roll_number="REP-001",
            email="report@example.com",
            course="Computer Science",
            gender="Male"
        )

    def test_export_pdf_view(self):
        response = self.client.get(reverse('export_report_card_pdf', args=[self.student.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="ReportCard_REP-001.pdf"', response['Content-Disposition'])
        self.assertTrue(len(response.content) > 1000)

    def test_pdf_generator_standalone(self):
        pdf_buffer = generate_report_card_pdf(self.student)
        self.assertTrue(len(pdf_buffer.getvalue()) > 1000)


class AnalyticsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='analytics_admin', password='password123')
        UserProfile.objects.update_or_create(user=self.admin, defaults={'role': 'Admin'})
        self.client.login(username='analytics_admin', password='password123')

    def test_analytics_data_structure(self):
        data = get_analytics_data()
        self.assertIn('total_students', data)
        self.assertIn('pass_rate', data)
        self.assertIn('overall_attendance_pct', data)
        self.assertIn('dept_labels_json', data)
        self.assertIn('dept_counts_json', data)

    def test_analytics_dashboard_view(self):
        response = self.client.get(reverse('analytics_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Institutional Analytics")
