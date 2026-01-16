"""
Instructor Dashboard API Views
Analytics and course management for instructors
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta

from course.models import Course
from result.models import Enrollment, Review
from payments.models import Transaction


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def instructor_dashboard(request):
    """
    Get instructor dashboard overview statistics
    """
    if not request.user.is_instructor:
        return Response(
            {"error": "Only instructors can access this endpoint"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get instructor's courses
    courses = Course.objects.filter(instructor=request.user)
    
    # Total statistics
    total_courses = courses.count()
    total_students = Enrollment.objects.filter(
        course__in=courses
    ).values('student').distinct().count()
    
    total_reviews = Review.objects.filter(course__in=courses).count()
    avg_rating = Review.objects.filter(
        course__in=courses
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Revenue statistics
    total_revenue = Transaction.objects.filter(
        course__in=courses,
        status='completed'
    ).aggregate(Sum('instructor_revenue'))['instructor_revenue__sum'] or 0
    
    # This month's statistics
    this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    this_month_enrollments = Enrollment.objects.filter(
        course__in=courses,
        enrolled_at__gte=this_month_start
    ).count()
    
    this_month_revenue = Transaction.objects.filter(
        course__in=courses,
        status='completed',
        created_at__gte=this_month_start
    ).aggregate(Sum('instructor_revenue'))['instructor_revenue__sum'] or 0
    
    # Recent enrollments
    recent_enrollments = Enrollment.objects.filter(
        course__in=courses
    ).select_related('student', 'course').order_by('-enrolled_at')[:10]
    
    recent_enrollments_data = [
        {
            'student_name': e.student.get_full_name() or e.student.username,
            'course_title': e.course.title,
            'enrolled_at': e.enrolled_at,
            'price_paid': float(e.price_paid)
        }
        for e in recent_enrollments
    ]
    
    # Course performance
    course_stats = []
    for course in courses[:10]:  # Top 10 courses
        course_stats.append({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'status': course.status,
            'total_enrollments': course.total_enrollments,
            'total_reviews': course.total_reviews,
            'average_rating': float(course.average_rating),
            'revenue': float(Transaction.objects.filter(
                course=course,
                status='completed'
            ).aggregate(Sum('instructor_revenue'))['instructor_revenue__sum'] or 0)
        })
    
    return Response({
        'overview': {
            'total_courses': total_courses,
            'total_students': total_students,
            'total_reviews': total_reviews,
            'average_rating': round(float(avg_rating), 2),
            'total_revenue': float(total_revenue),
        },
        'this_month': {
            'enrollments': this_month_enrollments,
            'revenue': float(this_month_revenue),
        },
        'recent_enrollments': recent_enrollments_data,
        'course_performance': course_stats,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_analytics(request, course_id):
    """
    Get detailed analytics for a specific course
    """
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found or you don't have permission"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Enrollment trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    enrollments_by_day = []
    
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = Enrollment.objects.filter(
            course=course,
            enrolled_at__gte=day_start,
            enrolled_at__lt=day_end
        ).count()
        
        enrollments_by_day.append({
            'date': day_start.date().isoformat(),
            'enrollments': count
        })
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        count = Review.objects.filter(course=course, rating=i).count()
        rating_distribution[f'{i}_star'] = count
    
    # Completion rate
    total_enrollments = course.total_enrollments
    completed_enrollments = Enrollment.objects.filter(
        course=course,
        completed_at__isnull=False
    ).count()
    
    completion_rate = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
    
    # Revenue breakdown
    revenue_data = Transaction.objects.filter(
        course=course,
        status='completed'
    ).aggregate(
        total_gross=Sum('gross_amount'),
        total_net=Sum('instructor_revenue'),
        total_fees=Sum('platform_fee')
    )
    
    return Response({
        'course_info': {
            'id': course.id,
            'title': course.title,
            'total_enrollments': course.total_enrollments,
            'total_reviews': course.total_reviews,
            'average_rating': float(course.average_rating),
        },
        'enrollment_trends': enrollments_by_day,
        'rating_distribution': rating_distribution,
        'completion_rate': round(completion_rate, 2),
        'revenue': {
            'gross_revenue': float(revenue_data['total_gross'] or 0),
            'net_revenue': float(revenue_data['total_net'] or 0),
            'platform_fees': float(revenue_data['total_fees'] or 0),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_progress_report(request, course_id):
    """
    Get student progress report for a course
    """
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    enrollments = Enrollment.objects.filter(
        course=course
    ).select_related('student').order_by('-progress_percent')
    
    students_data = []
    for enrollment in enrollments:
        students_data.append({
            'student_name': enrollment.student.get_full_name() or enrollment.student.username,
            'student_email': enrollment.student.email,
            'enrolled_at': enrollment.enrolled_at,
            'progress_percent': float(enrollment.progress_percent),
            'completed': enrollment.completed_at is not None,
            'last_accessed': enrollment.last_accessed,
        })
    
    return Response({
        'course_title': course.title,
        'total_students': len(students_data),
        'students': students_data
    })
