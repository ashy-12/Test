from django.urls import path
from . import views

urlpatterns = [
    # Core Student Directory & Admin Dashboard
    path('', views.student_list, name='student_list'),
    
    # Authentication & Role Navigation
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Custom Role Dashboards
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/grade/save/', views.teacher_save_grade, name='teacher_save_grade'),
    path('teacher/attendance/save/', views.teacher_save_attendance, name='teacher_save_attendance'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Bulk CSV Import
    path('import-csv/', views.import_students_csv_view, name='import_csv'),
    path('sample-csv/', views.download_sample_csv_view, name='sample_csv'),
    
    # PDF Report Card / Transcript Export
    path('student/<int:pk>/report-card/', views.export_report_card_pdf_view, name='export_report_card_pdf'),
    
    # Interactive Analytics Dashboard
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),

    # Existing CRUD Operations
    path('student/<int:pk>/', views.student_detail, name='student_detail'),
    path('student/add/', views.student_create, name='student_create'),
    path('student/<int:pk>/edit/', views.student_update, name='student_update'),
    path('student/<int:pk>/delete/', views.student_delete, name='student_delete'),
]
