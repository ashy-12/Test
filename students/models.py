from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Student(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    COURSE_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Mechanical Engineering', 'Mechanical Engineering'),
        ('Civil Engineering', 'Civil Engineering'),
        ('Electrical Engineering', 'Electrical Engineering'),
        ('Business Administration', 'Business Administration'),
        ('Data Science', 'Data Science'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    roll_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    course = models.CharField(max_length=50, choices=COURSE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.roll_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def cumulative_attendance_percentage(self):
        total = self.attendance_records.count()
        if total == 0:
            return 100.0  # Default to 100% if no records yet
        present = self.attendance_records.filter(status__in=['Present', 'Late']).count()
        return round((present / total) * 100, 1)

    @property
    def attendance_summary(self):
        total = self.attendance_records.count()
        present = self.attendance_records.filter(status='Present').count()
        late = self.attendance_records.filter(status='Late').count()
        absent = self.attendance_records.filter(status='Absent').count()
        percentage = self.cumulative_attendance_percentage
        return {
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'percentage': percentage,
        }

    @property
    def average_marks(self):
        grades = self.grades.all()
        if not grades.exists():
            return 0.0
        percentages = [(float(g.marks_obtained) / float(g.max_marks) * 100) for g in grades if g.max_marks > 0]
        return round(sum(percentages) / len(percentages), 1) if percentages else 0.0

    def create_portal_user(self, password=None):
        """
        Creates or updates a Django User account for this student.
        Username is the student's Roll Number (e.g. CS-2026-001).
        Default Password is 'Student@123' if not specified.
        """
        from django.contrib.auth.models import User
        username = self.roll_number.strip()

        # Find existing user by roll number or email
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            user = User.objects.filter(email__iexact=self.email).first()

        raw_password = password or "Student@123"

        if not user:
            user = User.objects.create_user(
                username=username,
                email=self.email,
                password=raw_password,
                first_name=self.first_name,
                last_name=self.last_name,
            )
        else:
            user.username = username
            user.first_name = self.first_name
            user.last_name = self.last_name
            user.email = self.email
            if password:
                user.set_password(password)
            user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'Student'
        profile.student = self
        profile.save()
        return user


@receiver(post_save, sender=Student)
def student_auto_create_user(sender, instance, created, **kwargs):
    if created:
        instance.create_portal_user()



class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Teacher', 'Teacher'),
        ('Student', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Admin')
    student = models.OneToOneField(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_profile')
    department = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'Admin' or self.user.is_superuser

    @property
    def is_teacher(self):
        return self.role == 'Teacher'

    @property
    def is_student(self):
        return self.role == 'Student'


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'Admin' if instance.is_superuser else 'Student'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
    else:
        if not hasattr(instance, 'profile'):
            role = 'Admin' if instance.is_superuser else 'Student'
            UserProfile.objects.get_or_create(user=instance, defaults={'role': role})


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, choices=Student.COURSE_CHOICES)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taught_subjects')

    def __str__(self):
        return f"{self.name} ({self.code})"


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    grade_letter = models.CharField(max_length=5, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject')
        ordering = ['subject__code']

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.code}: {self.marks_obtained}/{self.max_marks} ({self.grade_letter})"

    def calculate_grade(self):
        if not self.max_marks or self.max_marks <= 0:
            return 'N/A'
        pct = (float(self.marks_obtained) / float(self.max_marks)) * 100
        if pct >= 90:
            return 'A+'
        elif pct >= 80:
            return 'A'
        elif pct >= 70:
            return 'B'
        elif pct >= 60:
            return 'C'
        elif pct >= 50:
            return 'D'
        else:
            return 'F'

    def save(self, *args, **kwargs):
        if not self.grade_letter:
            self.grade_letter = self.calculate_grade()
        super().save(*args, **kwargs)


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    remarks = models.CharField(max_length=150, blank=True)

    class Meta:
        unique_together = ('student', 'subject', 'date')
        ordering = ['-date']

    def __str__(self):
        subj = self.subject.code if self.subject else 'General'
        return f"{self.student.roll_number} - {subj} - {self.date}: {self.status}"
