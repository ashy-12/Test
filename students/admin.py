from django.contrib import admin
from .models import Student, UserProfile, Subject, Grade, Attendance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'full_name', 'email', 'course', 'gender', 'enrollment_date')
    list_filter = ('course', 'gender', 'enrollment_date')
    search_fields = ('first_name', 'last_name', 'roll_number', 'email')
    ordering = ('roll_number',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'student')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'user__email', 'student__roll_number')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'teacher')
    list_filter = ('department', 'teacher')
    search_fields = ('code', 'name')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'marks_obtained', 'max_marks', 'grade_letter')
    list_filter = ('grade_letter', 'subject')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name', 'subject__name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date', 'status')
    list_filter = ('status', 'date', 'subject')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name')
