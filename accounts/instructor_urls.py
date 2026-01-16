"""
URL routing for instructor dashboard and analytics
"""
from django.urls import path
from . import instructor_api

app_name = 'instructor'

urlpatterns = [
    path('dashboard/', instructor_api.instructor_dashboard, name='dashboard'),
    path('analytics/<int:course_id>/', instructor_api.course_analytics, name='course-analytics'),
    path('students/<int:course_id>/', instructor_api.student_progress_report, name='student-progress'),
]
