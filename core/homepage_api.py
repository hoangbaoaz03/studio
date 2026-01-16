"""
Homepage and course discovery API views
Provides data for homepage, search, and browse pages
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
from django.core.cache import cache

from course.models import Course, Category
from result.models import Review
from accounts.models import InstructorProfile


@api_view(['GET'])
@permission_classes([AllowAny])
def homepage_data(request):
    """
    Get all data needed for homepage
    Cached for 5 minutes
    """
    cache_key = 'homepage_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    # Featured courses
    featured_courses = Course.objects.filter(
        status='published',
        is_featured=True
    ).select_related('instructor', 'category').order_by('-average_rating')[:8]
    
    # Popular courses (by enrollments)
    popular_courses = Course.objects.filter(
        status='published'
    ).select_related('instructor', 'category').order_by('-total_enrollments')[:8]
    
    # New courses
    new_courses = Course.objects.filter(
        status='published'
    ).select_related('instructor', 'category').order_by('-published_at')[:8]
    
    # Top rated courses
    top_rated = Course.objects.filter(
        status='published',
        average_rating__gte=4.5
    ).select_related('instructor', 'category').order_by('-average_rating')[:8]
    
    # Categories with course counts
    categories = Category.objects.filter(
        is_active=True
    ).order_by('order')[:12]
    
    # Featured instructors
    featured_instructors = InstructorProfile.objects.filter(
        is_featured=True,
        verified=True
    ).select_related('user').order_by('-total_students')[:8]
    
    # Stats
    total_courses = Course.objects.filter(status='published').count()
    total_students = cache.get('total_students') or 0
    total_reviews = Review.objects.count()
    
    # Serialize data
    from course.serializers import CourseListSerializer
    from accounts.serializers import InstructorProfileSerializer
    from course.serializers import CategorySerializer
    
    data = {
        'featured_courses': CourseListSerializer(featured_courses, many=True).data,
        'popular_courses': CourseListSerializer(popular_courses, many=True).data,
        'new_courses': CourseListSerializer(new_courses, many=True).data,
        'top_rated_courses': CourseListSerializer(top_rated, many=True).data,
        'categories': CategorySerializer(categories, many=True).data,
        'featured_instructors': InstructorProfileSerializer(featured_instructors, many=True).data,
        'stats': {
            'total_courses': total_courses,
            'total_students': total_students,
            'total_reviews': total_reviews,
        }
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, data, 300)
    
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_courses(request):
    """
    Advanced course search
    Query params:
    - q: search query
    - category: category ID
    - level: beginner/intermediate/advanced
    - price: free/paid
    - rating: minimum rating (1-5)
    - sort: newest/popular/rating/price_low/price_high
    """
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    level = request.GET.get('level')
    price_filter = request.GET.get('price')
    min_rating = request.GET.get('rating')
    sort_by = request.GET.get('sort', 'popular')
    
    # Start with published courses
    courses = Course.objects.filter(status='published')
    
    # Text search
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(subtitle__icontains=query) |
            Q(description__icontains=query) |
            Q(instructor__first_name__icontains=query) |
            Q(instructor__last_name__icontains=query)
        )
    
    # Category filter
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    # Level filter
    if level:
        courses = courses.filter(level=level)
    
    # Price filter
    if price_filter == 'free':
        courses = courses.filter(is_free=True)
    elif price_filter == 'paid':
        courses = courses.filter(is_free=False)
    
    # Rating filter
    if min_rating:
        courses = courses.filter(average_rating__gte=float(min_rating))
    
    # Sorting
    if sort_by == 'newest':
        courses = courses.order_by('-published_at')
    elif sort_by == 'rating':
        courses = courses.order_by('-average_rating')
    elif sort_by == 'price_low':
        courses = courses.order_by('price')
    elif sort_by == 'price_high':
        courses = courses.order_by('-price')
    else:  # popular
        courses = courses.order_by('-total_enrollments')
    
    # Pagination
    from rest_framework.pagination import PageNumberPagination
    
    paginator = PageNumberPagination()
    paginator.page_size = 20
    result_page = paginator.paginate_queryset(courses, request)
    
    from course.serializers import CourseListSerializer
    serializer = CourseListSerializer(result_page, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def category_courses(request, slug):
    """
    Get all courses in a category
    """
    try:
        category = Category.objects.get(slug=slug, is_active=True)
    except Category.DoesNotExist:
        return Response(
            {"error": "Category not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    courses = Course.objects.filter(
        category=category,
        status='published'
    ).select_related('instructor').order_by('-total_enrollments')
    
    # Pagination
    from rest_framework.pagination import PageNumberPagination
    
    paginator = PageNumberPagination()
    paginator.page_size = 20
    result_page = paginator.paginate_queryset(courses, request)
    
    from course.serializers import CourseListSerializer
    serializer = CourseListSerializer(result_page, many=True)
    
    return paginator.get_paginated_response({
        'category': {
            'name': category.name,
            'description': category.description,
            'total_courses': courses.count()
        },
        'courses': serializer.data
    })


@api_view(['GET'])
@permission_classes([AllowAny])  
def instructor_profile(request, instructor_id):
    """
    Get instructor public profile with their courses
    """
    try:
        instructor = InstructorProfile.objects.get(
            user_id=instructor_id
        )
    except InstructorProfile.DoesNotExist:
        return Response(
            {"error": "Instructor not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Instructor's published courses
    courses = Course.objects.filter(
        instructor_id=instructor_id,
        status='published'
    ).order_by('-published_at')
    
    from accounts.serializers import InstructorProfileSerializer
    from course.serializers import CourseListSerializer
    
    return Response({
        'instructor': InstructorProfileSerializer(instructor).data,
        'courses': CourseListSerializer(courses, many=True).data
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_courses(request):
    """
    Get trending courses (based on recent enrollments)
    """
    from datetime import timedelta
    from django.utils import timezone
    from result.models import Enrollment
    
    # Courses with most enrollments in last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    trending = Course.objects.filter(
        status='published',
        enrollments__enrolled_at__gte=seven_days_ago
    ).annotate(
        recent_enrollments=Count('enrollments')
    ).order_by('-recent_enrollments')[:12]
    
    from course.serializers import CourseListSerializer
    return Response(CourseListSerializer(trending, many=True).data)
