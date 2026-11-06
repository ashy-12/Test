import json
from django.db.models import Count, Avg
from .models import Student, Subject, Grade, Attendance


def get_analytics_data():
    """
    Computes comprehensive analytics across students, departments,
    attendance, and academic performance for modern Chart.js visualization.
    """
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    total_grades = Grade.objects.count()

    # 1. Total students enrolled by department
    dept_qs = Student.objects.values('course').annotate(count=Count('id')).order_by('-count')
    dept_labels = [item['course'] for item in dept_qs]
    dept_counts = [item['count'] for item in dept_qs]

    # 2. Department-wide attendance averages
    dept_attendance_labels = []
    dept_attendance_values = []
    
    # Check all active departments
    active_depts = list(Student.objects.values_list('course', flat=True).distinct())
    for dept in active_depts:
        total_att = Attendance.objects.filter(student__course=dept).count()
        if total_att > 0:
            present_att = Attendance.objects.filter(student__course=dept, status__in=['Present', 'Late']).count()
            avg_pct = round((present_att / total_att) * 100, 1)
        else:
            avg_pct = 95.0  # Baseline if no records yet
        dept_attendance_labels.append(dept)
        dept_attendance_values.append(avg_pct)

    # Overall system attendance average
    sys_total_att = Attendance.objects.count()
    if sys_total_att > 0:
        sys_present_att = Attendance.objects.filter(status__in=['Present', 'Late']).count()
        overall_attendance_pct = round((sys_present_att / sys_total_att) * 100, 1)
    else:
        overall_attendance_pct = 95.0

    # 3. Grade distributions and Pass/Fail rates
    grade_order = ['A+', 'A', 'B', 'C', 'D', 'F']
    grade_counts_dict = {k: 0 for k in grade_order}

    for item in Grade.objects.values('grade_letter').annotate(count=Count('id')):
        letter = item['grade_letter']
        if letter in grade_counts_dict:
            grade_counts_dict[letter] = item['count']
        elif letter:
            grade_counts_dict['C'] = grade_counts_dict.get('C', 0) + item['count']

    grade_labels = grade_order
    grade_counts = [grade_counts_dict[k] for k in grade_order]

    passed_count = sum(grade_counts_dict[k] for k in ['A+', 'A', 'B', 'C', 'D'])
    failed_count = grade_counts_dict.get('F', 0)
    graded_total = passed_count + failed_count
    pass_rate = round((passed_count / graded_total) * 100, 1) if graded_total > 0 else 100.0

    # 4. Gender distribution
    gender_labels = ['Male', 'Female', 'Other']
    gender_counts = [
        Student.objects.filter(gender='Male').count(),
        Student.objects.filter(gender='Female').count(),
        Student.objects.filter(gender='Other').count(),
    ]

    return {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_grades': total_grades,
        'overall_attendance_pct': overall_attendance_pct,
        'pass_rate': pass_rate,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'dept_labels_json': json.dumps(dept_labels),
        'dept_counts_json': json.dumps(dept_counts),
        'dept_attendance_labels_json': json.dumps(dept_attendance_labels),
        'dept_attendance_values_json': json.dumps(dept_attendance_values),
        'grade_labels_json': json.dumps(grade_labels),
        'grade_counts_json': json.dumps(grade_counts),
        'gender_labels_json': json.dumps(gender_labels),
        'gender_counts_json': json.dumps(gender_counts),
    }
