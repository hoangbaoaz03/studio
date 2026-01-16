"""
Course recommendation engine
Provides personalized course recommendations
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q, Avg
from django.core.cache import cache

from course.models import Course, Category
from result.models import Enrollment, Review
from accounts.models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_for_you(request):
    """
    Personalized recommendations based on:
    - Enrolled courses
    - Wishlisted courses
    - Browsing history (if available)
    - Popular courses in same categories
    """
    user = request.user
    
    # Get user's enrolled courses
    enrolled_courses = Enrollment.objects.filter(
        student=user
    ).values_list('course_id', flat=True)
    
    # Get categories of enrolled courses
    enrolled_categories = Course.objects.filter(
        id__in=enrolled_courses
    ).values_list('category_id', flat=True).distinct()
    
    # Recommend courses in same categories
    recommended = Course.objects.filter(
        category_id__in=enrolled_categories,
        status='published'
    ).exclude(
        id__in=enrolled_courses
    ).order_by('-average_rating', '-total_enrollments')[:12]
    
    # If not enough recommendations, add popular courses
    if recommended.count() < 12:
        popular = Course.objects.filter(
            status='published'
        ).exclude(
            id__in=enrolled_courses
        ).order_by('-total_enrollments')[:12 - recommended.count()]
        
        recommended = list(recommended) + list(popular)
    
    from course.serializers import CourseListSerializer
    return Response({
        'recommendations': CourseListSerializer(recommended, many=True).data,
        'reason': 'Based on your learning interests'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def similar_courses(request, course_id):
    """
    Find courses similar to a given course
    Based on category, instructor, and tags
    """
    try:
        course = Course.objects.get(id=course_id, status='published')
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    
    # Find similar courses
    similar = Course.objects.filter(
        Q(category=course.category) | Q(subcategory=course.subcategory),
        status='published'
    ).exclude(
        id=course_id
    ).order_by('-average_rating')[:8]
    
    # Also include courses by same instructor
    by_instructor = Course.objects.filter(
        instructor=course.instructor,
        status='published'
    ).exclude(
        id=course_id
    ).order_by('-total_enrollments')[:4]
    
    from course.serializers import CourseListSerializer
    return Response({
        'similar_courses': CourseListSerializer(similar, many=True).data,
        'more_by_instructor': CourseListSerializer(by_instructor, many=True).data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def students_also_bought(request, course_id):
    """
    Courses frequently bought together
    Based on enrollment patterns
    """
    try:
        course = Course.objects.get(id=course_id, status='published')
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    
    # Get students who enrolled in this course
    students_in_course = Enrollment.objects.filter(
        course=course
    ).values_list('student_id', flat=True)
    
    # Find what other courses these students enrolled in
    also_bought = Course.objects.filter(
        enrollments__student_id__in=students_in_course,
        status='published'
    ).exclude(
        id=course_id
    ).annotate(
        common_students=Count('enrollments')
    ).order_by('-common_students', '-average_rating')[:8]
    
    from course.serializers import CourseListSerializer
    return Response({
        'courses': CourseListSerializer(also_bought, many=True).data,
        'title': 'Students also bought'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def top_rated_in_category(request, category_id):
    """
    Top rated courses in a specific category
    """
    cache_key = f'top_rated_category_{category_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        category = Category.objects.get(id=category_id, is_active=True)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)
    
    top_courses = Course.objects.filter(
        category=category,
        status='published',
        average_rating__gte=4.0
    ).order_by('-average_rating', '-total_reviews')[:12]
    
    from course.serializers import CourseListSerializer
    data = {
        'category': category.name,
        'courses': CourseListSerializer(top_courses, many=True).data
    }
    
    # Cache for 10 minutes
    cache.set(cache_key, data, 600)
    
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def because_you_viewed(request, course_id):
    """
    Recommendations based on viewing a course
    """
    try:
        viewed_course = Course.objects.get(id=course_id, status='published')
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    
    # Recommend similar level courses in same category
    recommendations = Course.objects.filter(
        category=viewed_course.category,
        level=viewed_course.level,
        status='published'
    ).exclude(
        id=course_id
    ).order_by('-average_rating')[:8]
    
    from course.serializers import CourseListSerializer
    return Response({
        'courses': CourseListSerializer(recommendations, many=True).data,
        'title': f'Because you viewed "{viewed_course.title}"'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_homepage(request):
    """
    Personalized homepage sections for logged-in user
    """
    user = request.user
    
    # Get user's enrolled courses
    enrollments = Enrollment.objects.filter(student=user)
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    enrolled_categories = Course.objects.filter(
        id__in=enrolled_course_ids
    ).values_list('category_id', flat=True).distinct()
    
    # Continue learning
    continue_learning = enrollments.filter(
        completed_at__isnull=True
    ).select_related('course').order_by('-last_accessed')[:6]
    
    # Recommended based on interests
    recommended = Course.objects.filter(
        category_id__in=enrolled_categories,
        status='published'
    ).exclude(
        id__in=enrolled_course_ids
    ).order_by('-average_rating')[:8]
    
    # New in your interests
    new_in_interests = Course.objects.filter(
        category_id__in=enrolled_categories,
        status='published'
    ).exclude(
        id__in=enrolled_course_ids
    ).order_by('-published_at')[:8]
    
    from course.serializers import CourseListSerializer
    from result.serializers import EnrollmentSerializer
    
    return Response({
        'continue_learning': [{
            'enrollment': EnrollmentSerializer(e).data,
            'course': CourseListSerializer(e.course).data
        } for e in continue_learning],
        'recommended_for_you': CourseListSerializer(recommended, many=True).data,
        'new_in_interests': CourseListSerializer(new_in_interests, many=True).data,
    })
