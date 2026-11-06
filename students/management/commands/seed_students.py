from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from students.models import Student, UserProfile, Subject, Grade, Attendance


class Command(BaseCommand):
    help = 'Seeds initial sample students, roles, subjects, grades, and attendance'

    def handle(self, *args, **options):
        # 1. Create or update sample users and profiles
        # Admin
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('admin123')
        admin_user.save()
        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        admin_profile.role = 'Admin'
        admin_profile.save()

        # Teacher
        teacher_user, _ = User.objects.get_or_create(
            username='teacher',
            defaults={'email': 'teacher@example.com', 'first_name': 'Prof. Rajesh', 'last_name': 'Kulkarni'}
        )
        teacher_user.set_password('teacher123')
        teacher_user.save()
        teacher_profile, _ = UserProfile.objects.get_or_create(user=teacher_user)
        teacher_profile.role = 'Teacher'
        teacher_profile.department = 'Computer Science'
        teacher_profile.save()

        # 2. Seed Students
        sample_students = [
            {
                'first_name': 'Aarav',
                'last_name': 'Sharma',
                'roll_number': 'CS-2026-001',
                'email': 'aarav.sharma@example.com',
                'phone': '+91 98765 43210',
                'gender': 'Male',
                'course': 'Computer Science',
                'date_of_birth': date(2003, 5, 14),
                'enrollment_date': date(2023, 8, 1),
                'address': '124 MG Road, Bangalore, Karnataka',
            },
            {
                'first_name': 'Priya',
                'last_name': 'Patel',
                'roll_number': 'IT-2026-002',
                'email': 'priya.patel@example.com',
                'phone': '+91 98234 56789',
                'gender': 'Female',
                'course': 'Information Technology',
                'date_of_birth': date(2003, 9, 21),
                'enrollment_date': date(2023, 8, 1),
                'address': '45 Park Street, Ahmedabad, Gujarat',
            },
            {
                'first_name': 'Rohan',
                'last_name': 'Verma',
                'roll_number': 'DS-2026-003',
                'email': 'rohan.verma@example.com',
                'phone': '+91 91234 56780',
                'gender': 'Male',
                'course': 'Data Science',
                'date_of_birth': date(2002, 11, 3),
                'enrollment_date': date(2022, 8, 1),
                'address': '78 Sector 18, Noida, Uttar Pradesh',
            },
            {
                'first_name': 'Ananya',
                'last_name': 'Iyer',
                'roll_number': 'CS-2026-004',
                'email': 'ananya.iyer@example.com',
                'phone': '+91 97890 12345',
                'gender': 'Female',
                'course': 'Computer Science',
                'date_of_birth': date(2004, 2, 18),
                'enrollment_date': date(2024, 8, 1),
                'address': '22 Cathedral Road, Chennai, Tamil Nadu',
            },
            {
                'first_name': 'Kabir',
                'last_name': 'Singh',
                'roll_number': 'ME-2026-005',
                'email': 'kabir.singh@example.com',
                'phone': '+91 98111 22334',
                'gender': 'Male',
                'course': 'Mechanical Engineering',
                'date_of_birth': date(2003, 7, 30),
                'enrollment_date': date(2023, 8, 1),
                'address': '15 Civil Lines, Jaipur, Rajasthan',
            },
            {
                'first_name': 'Sneha',
                'last_name': 'Reddy',
                'roll_number': 'BA-2026-006',
                'email': 'sneha.reddy@example.com',
                'phone': '+91 99887 76655',
                'gender': 'Female',
                'course': 'Business Administration',
                'date_of_birth': date(2003, 1, 10),
                'enrollment_date': date(2023, 8, 1),
                'address': '89 Jubilee Hills, Hyderabad, Telangana',
            },
        ]

        created_students = []
        for item in sample_students:
            student, _ = Student.objects.update_or_create(
                roll_number=item['roll_number'],
                defaults=item
            )
            created_students.append(student)

        # Student User (linked to Aarav Sharma)
        first_student = Student.objects.filter(roll_number='CS-2026-001').first()
        student_user, _ = User.objects.get_or_create(
            username='student',
            defaults={'email': 'aarav.sharma@example.com', 'first_name': 'Aarav', 'last_name': 'Sharma'}
        )
        student_user.set_password('student123')
        student_user.save()
        student_profile, _ = UserProfile.objects.get_or_create(user=student_user)
        student_profile.role = 'Student'
        student_profile.student = first_student
        student_profile.save()

        # 3. Seed Subjects
        subjects_data = [
            {'code': 'CS-301', 'name': 'Data Structures & Algorithms', 'department': 'Computer Science', 'teacher': teacher_user},
            {'code': 'CS-302', 'name': 'Database Management Systems', 'department': 'Computer Science', 'teacher': teacher_user},
            {'code': 'CS-303', 'name': 'Operating Systems', 'department': 'Computer Science', 'teacher': teacher_user},
            {'code': 'IT-201', 'name': 'Web Technologies & Frameworks', 'department': 'Information Technology', 'teacher': teacher_user},
            {'code': 'DS-101', 'name': 'Probability & Statistics for AI', 'department': 'Data Science', 'teacher': teacher_user},
        ]

        created_subjects = []
        for s_data in subjects_data:
            subj, _ = Subject.objects.update_or_create(
                code=s_data['code'],
                defaults=s_data
            )
            created_subjects.append(subj)

        # 4. Seed Grades
        grades_data = [
            {'student': created_students[0], 'subject': created_subjects[0], 'marks_obtained': 92.5, 'max_marks': 100.0, 'remarks': 'Excellent algorithm design'},
            {'student': created_students[0], 'subject': created_subjects[1], 'marks_obtained': 88.0, 'max_marks': 100.0, 'remarks': 'Great SQL proficiency'},
            {'student': created_students[0], 'subject': created_subjects[2], 'marks_obtained': 85.0, 'max_marks': 100.0, 'remarks': 'Very good conceptual grasp'},
            {'student': created_students[1], 'subject': created_subjects[3], 'marks_obtained': 91.0, 'max_marks': 100.0, 'remarks': 'Superb frontend implementation'},
            {'student': created_students[2], 'subject': created_subjects[4], 'marks_obtained': 78.0, 'max_marks': 100.0, 'remarks': 'Good understanding of distributions'},
            {'student': created_students[3], 'subject': created_subjects[0], 'marks_obtained': 95.0, 'max_marks': 100.0, 'remarks': 'Top scoring performance'},
            {'student': created_students[3], 'subject': created_subjects[1], 'marks_obtained': 89.5, 'max_marks': 100.0, 'remarks': 'Clear normalization analysis'},
        ]

        for g in grades_data:
            grade, _ = Grade.objects.update_or_create(
                student=g['student'],
                subject=g['subject'],
                defaults={
                    'marks_obtained': g['marks_obtained'],
                    'max_marks': g['max_marks'],
                    'remarks': g['remarks'],
                }
            )

        # 5. Seed Attendance
        today = timezone.now().date()
        for idx, student in enumerate(created_students):
            # 10 recent lecture dates
            for d in range(10):
                att_date = today - timedelta(days=d)
                # Vary attendance slightly
                status = 'Present'
                if idx == 0 and d == 3:
                    status = 'Late'
                elif idx == 1 and d == 5:
                    status = 'Absent'
                elif idx == 4 and d in [2, 4, 7]:
                    status = 'Absent'

                # Use primary subject for this student's course
                subj = created_subjects[0] if student.course == 'Computer Science' else (
                    created_subjects[3] if student.course == 'Information Technology' else created_subjects[4]
                )

                Attendance.objects.update_or_create(
                    student=student,
                    subject=subj,
                    date=att_date,
                    defaults={'status': status}
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded students, roles, subjects, grades, and attendance!'))
