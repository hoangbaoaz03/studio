"""
API Views for Course endpoints
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Subcategory, Course, Section, Lecture
from .serializers import (
    CategorySerializer,
    SubcategorySerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    SectionSerializer,
    LectureSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for course categories
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, slug=None):
        """Get all subcategories for a category"""
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True)
        serializer = SubcategorySerializer(subcategories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def courses(self, request, slug=None):
        """Get all courses in a category"""
        category = self.get_object()
        courses = Course.objects.filter(
            category=category,
            status='published'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = CourseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)


class SubcategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for subcategories
    """
    queryset = Subcategory.objects.filter(is_active=True)
    serializer_class = SubcategorySerializer
    lookup_field = 'slug'


class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for courses
    List/retrieve for all users, create/update for instructors only
    """
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'level', 'language', 'is_free']
    search_fields = ['title', 'subtitle', 'description']
    ordering_fields = ['created_at', 'average_rating', 'total_enrollments', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Course.objects.filter(status='published')
        
        # Filter by instructor (for instructor dashboard)
        instructor_id = self.request.query_params.get('instructor', None)
        if instructor_id:
            queryset = Course.objects.filter(instructor_id=instructor_id)
        
        # Price range filter
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Rating filter
        min_rating = self.request.query_params.get('min_rating', None)
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer
    
    def perform_create(self, serializer):
        # Ensure user is an instructor
        if not self.request.user.is_instructor:
            raise PermissionError("Only instructors can create courses")
        serializer.save(instructor=self.request.user)
    
    def perform_update(self, serializer):
        # Ensure user owns the course
        course = self.get_object()
        if course.instructor != self.request.user:
            raise PermissionError("You can only edit your own courses")
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def curriculum(self, request, slug=None):
        """Get detailed curriculum for a course"""
        course = self.get_object()
        sections = course.sections.all()
        serializer = SectionSerializer(sections, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured courses"""
        courses = Course.objects.filter(
            status='published',
            is_featured=True
        ).order_by('-average_rating')[:12]
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular courses by enrollment"""
        courses = Course.objects.filter(
            status='published'
        ).order_by('-total_enrollments')[:12]
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """Get courses created by the authenticated instructor"""
        if not request.user.is_instructor:
            return Response(
                {"error": "Only instructors can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        courses = Course.objects.filter(instructor=request.user).order_by('-created_at')
        serializer = CourseDetailSerializer(courses, many=True)
        return Response(serializer.data)


class SectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course sections
    Only course instructor can create/update
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Verify user owns the course
        course_id = self.request.data.get('course')
        course = Course.objects.get(id=course_id)
        if course.instructor != self.request.user:
            raise PermissionError("You can only add sections to your own courses")
        serializer.save()


class LectureViewSet(viewsets.ModelViewSet):
    """
    API endpoint for lectures
    Only course instructor can create/update
    """
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Verify user owns the course
        section_id = self.request.data.get('section')
        section = Section.objects.get(id=section_id)
        if section.course.instructor != self.request.user:
            raise PermissionError("You can only add lectures to your own courses")
        serializer.save()
