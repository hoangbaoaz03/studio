"""
API Views for Course endpoints
"""
from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

from .models import Category, Subcategory, Course, Section, Lecture, Announcement
from .serializers import (
    CategorySerializer,
    CategoryTreeSerializer,
    SubcategorySerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    SectionSerializer,
    LectureSerializer,
    AnnouncementSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for course categories
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly], authentication_classes=[])
    def tree(self, request):
        """
        Get the full category tree (Root -> Children -> Grandchildren)
        Optimized with mptt's get_cached_trees or prefetch
        """
        # Fetch all attributes to let MPTT build the tree in Python
        # distinct() is not needed unless joins duplicate rows, but safe to keep if filtering
        # get_cached_trees returns a list of top-level nodes with .children populated
        roots = Category.objects.filter(is_active=True).get_cached_trees()
        serializer = CategoryTreeSerializer(roots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def courses(self, request, slug=None):
        """Get all courses in a category and its descendants"""
        category = self.get_object()
        # MPTT optimization: get all descendants including self
        categories = category.get_descendants(include_self=True)
        
        courses = Course.objects.filter(
            category__in=categories,
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
        # By default show all for admins or logic below
        # For public list: published only
        # For retrieve: published OR owner
        
        queryset = Course.objects.all()

        # By default exclude deleted, unless accessing trash/restore/permanent_delete
        if self.action not in ['trash', 'restore', 'permanent_delete']:
             queryset = queryset.filter(is_deleted=False)
        
        if self.action == 'list':
            # Public listing always filtered to published unless specific filters applied (like my_courses uses its own)
            # Actually standard list should be published only
            queryset = queryset.filter(status='published')

            # Filter by instructor (for instructor dashboard public view)
            instructor_id = self.request.query_params.get('instructor', None)
            if instructor_id:
                queryset = queryset.filter(courseinstructors__instructor_id=instructor_id)
            
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
            
        elif self.action == 'retrieve':
             # Allow if published OR if user matches instructor (owner)
             # Relaxing check: user.is_instructor not strictly required for ownership check
             user = self.request.user
             if user.is_authenticated:
                 if user.is_staff or user.is_superuser:
                     return queryset # Admin can view ANY course
                 from django.db.models import Q
                 return queryset.filter(Q(status='published') | Q(courseinstructors__instructor=user))
             return queryset.filter(status='published')
             
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
        from .models import CourseInstructor
        course = serializer.save()
        # Create M2M link as primary instructor
        CourseInstructor.objects.get_or_create(
            course=course,
            instructor=self.request.user,
            defaults={'is_primary': True}
        )
    
    def perform_update(self, serializer):
        # Ensure user owns the course
        course = self.get_object()
        if not course.courseinstructors.filter(instructor=self.request.user).exists():
            raise PermissionError("You can only edit your own courses")
        serializer.save()
        
    def destroy(self, request, *args, **kwargs):
        course = self.get_object()
        if not course.courseinstructors.filter(instructor=request.user).exists():
             return Response({"error": "Not authorized"}, status=403)
        course.is_deleted = True
        from django.utils import timezone
        course.deleted_at = timezone.now()
        course.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def trash(self, request):
        """List soft-deleted courses for instructor"""
        courses = Course.objects.filter(courseinstructors__instructor=request.user, is_deleted=True).order_by('-deleted_at')
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restore(self, request, slug=None):
        """Restore a soft-deleted course"""
        course = self.get_object()
        if not course.courseinstructors.filter(instructor=request.user).exists():
             return Response({"error": "Not authorized"}, status=403)
        course.is_deleted = False
        course.deleted_at = None
        course.save()
        return Response({"status": "restored"})

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def permanent_delete(self, request, slug=None):
        """Permanently delete a course"""
        course = self.get_object()
        if not course.courseinstructors.filter(instructor=request.user).exists():
             return Response({"error": "Not authorized"}, status=403)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly], authentication_classes=[])
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
        
        courses = Course.objects.filter(courseinstructors__instructor=request.user).order_by('-created_at')
        serializer = CourseDetailSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly], authentication_classes=[])
    def related(self, request, slug=None):
        """
        Get related courses (same category, excluding self)
        """
        course = self.get_object()
        
        # Get courses in the same category (or descendants)
        if course.category:
            categories = course.category.get_descendants(include_self=True)
            related_courses = Course.objects.filter(
                category__in=categories,
                status='published'
            ).exclude(id=course.id).order_by('-total_enrollments')[:10] # Show popular ones first
        else:
            related_courses = Course.objects.none()
            
        serializer = CourseListSerializer(related_courses, many=True)
        return Response(serializer.data)


class SectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course sections
    Only course instructor can create/update
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        print(f"DEBUG: Section Create Data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"DEBUG: Section Serializer Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        # Verify user owns the course
        course = serializer.validated_data.get('course')
        if not course:
            # Should be handled by serializer validation, but safe check
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"course": "Course is required"})
            
        if not course.courseinstructors.filter(instructor=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add sections to your own courses")
        serializer.save()

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder sections within a course.
        Expects payload: { "course_id": 1, "section_ids": [3, 1, 2] }
        """
        course_id = request.data.get('course_id')
        section_ids = request.data.get('section_ids', [])
        
        if not course_id or not section_ids:
            return Response(
                {"error": "course_id and section_ids required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        course = Course.objects.get(id=course_id)
        if not course.courseinstructors.filter(instructor=request.user).exists():
            return Response(
                {"error": "Not authorized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Bulk update order (Naive approach)
        sections = []
        for index, s_id in enumerate(section_ids):
            try:
                section = Section.objects.get(id=s_id, course_id=course_id)
                section.order = index
                sections.append(section)
            except Section.DoesNotExist:
                continue
                
        Section.objects.bulk_update(sections, ['order'])
        return Response({"status": "reordered"})


class LectureViewSet(viewsets.ModelViewSet):
    """
    API endpoint for lectures
    Only course instructor can create/update
    """
    queryset = Lecture.objects.all()
    serializer_class = LectureSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        print(f"DEBUG: Lecture Create Data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print(f"DEBUG: Lecture Serializer Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        
        # If this is a quiz lecture, save quiz_data if provided
        if request.data.get('lecture_type') == 'quiz':
            import json
            quiz_data_raw = request.data.get('quiz_data')
            if quiz_data_raw:
                from .models import QuizQuestion, QuizAnswer
                try:
                    quiz_data = json.loads(quiz_data_raw) if isinstance(quiz_data_raw, str) else quiz_data_raw
                    lecture_obj = Lecture.objects.get(id=serializer.data['id'])
                    for q_idx, q_data in enumerate(quiz_data):
                        question = QuizQuestion.objects.create(
                            lecture=lecture_obj,
                            question_text=q_data['question'],
                            explanation=q_data.get('explanation', ''),
                            order=q_idx
                        )
                        for choice_text in q_data['choices']:
                            is_correct = (choice_text.strip().lower() == q_data['correct_answer'].strip().lower())
                            QuizAnswer.objects.create(
                                question=question,
                                answer_text=choice_text,
                                is_correct=is_correct
                            )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        # Verify user owns the course
        section_id = self.request.data.get('section')
        if not section_id:
            raise serializers.ValidationError({"section": "This field is required."})
            
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            raise serializers.ValidationError({"section": "Invalid section ID."})
            
        if not section.course.courseinstructors.filter(instructor=self.request.user).exists():
            raise PermissionError("You can only add lectures to your own courses")
            
        serializer.save(section=section)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder lectures within a SECTION.
        Expects payload: { "section_id": 1, "lecture_ids": [10, 8, 9] }
        """
        section_id = request.data.get('section_id')
        lecture_ids = request.data.get('lecture_ids', [])
        
        if not section_id or not lecture_ids:
            return Response(
                {"error": "section_id and lecture_ids required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response({"error": "Invalid section"}, status=400)
            
        if not section.course.courseinstructors.filter(instructor=request.user).exists():
            return Response(
                {"error": "Not authorized"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        lectures = []
        for index, l_id in enumerate(lecture_ids):
            try:
                lecture = Lecture.objects.get(id=l_id, section_id=section_id)
                lecture.order = index
                lectures.append(lecture)
            except Lecture.DoesNotExist:
                continue
                
        Lecture.objects.bulk_update(lectures, ['order'])
        return Response({"status": "reordered"})

    @action(detail=True, methods=['post'])
    def upload_video(self, request, pk=None):
        """
        Get Presigned URL for video upload (Mock for MVP).
        Real implementation would use boto3 to generate S3 presigned POST.
        """
        lecture = self.get_object()
        if not lecture.section.course.courseinstructors.filter(instructor=request.user).exists():
             return Response({"error": "Not authorized"}, status=403)
             
        # Mock Response
        # In real world: generate UUID key -> boto3.generate_presigned_url
        key = f"courses/{lecture.section.course.id}/lectures/{lecture.id}/{request.data.get('filename', 'video.mp4')}"
        return Response({
            "upload_url": "https://s3.amazonaws.com/mock-bucket", 
            "fields": {"key": key, "AWSAccessKeyId": "MOCK"},
            "key": key
        })

    @action(detail=False, methods=['post'], url_path='preview-quiz')
    def preview_quiz(self, request):
        """
        Upload a document, parse it via AI, and return generated questions
        for preview WITHOUT saving anything to the database.
        """
        if not getattr(request.user, 'is_instructor', False):
            return Response({"error": "Only instructors can generate quizzes"}, status=status.HTTP_403_FORBIDDEN)
            
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            from .quiz_generator import extract_text_from_file, generate_quiz_from_text
            
            text = extract_text_from_file(file_obj, file_obj.name)
            if len(text) < 50:
                return Response({"error": "Could not extract enough text from the document."}, status=status.HTTP_400_BAD_REQUEST)
                
            questions_data = generate_quiz_from_text(text, num_questions=10)
            
            if not questions_data:
                return Response({"error": "AI could not generate questions from this text."}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({"questions": questions_data})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course announcements
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        if self.action == 'list':
            course_id = self.request.query_params.get('course_id')
            if course_id:
                return Announcement.objects.filter(course_id=course_id).order_by('-created_at')
            return Announcement.objects.none()
        return Announcement.objects.all()
        
    def perform_create(self, serializer):
        course_id = self.request.data.get('course_id')
        if not course_id:
            # Try from URL or context if available, or error
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Course ID required")
            
        course = Course.objects.get(id=course_id)
        # Verify instructor
        if not course.courseinstructors.filter(instructor=self.request.user).exists():
             from rest_framework.exceptions import PermissionDenied
             raise PermissionDenied("Only course instructor can post announcements")
        
        announcement = serializer.save(user=self.request.user, course=course)
        
        # Notify enrolled students
        from result.models import Enrollment
        from core.models import Notification
        
        enrollments = Enrollment.objects.filter(course=course).select_related('student')
        notifications = []
        for enrollment in enrollments:
            notifications.append(
                Notification(
                    recipient=enrollment.student,
                    title=f"New Announcement in {course.title}",
                    message=f"{self.request.user.get_full_name()} posted: '{announcement.title}'",
                    notification_type='course',
                    link=f"/course/{course.slug}/learn?tab=announcements"
                )
            )
        if notifications:
            Notification.objects.bulk_create(notifications)
        
        # Push notification via WebSocket to each enrolled student
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        
        for enrollment in enrollments:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{enrollment.student.id}",
                {"type": "send_notification", "data": {"event": "new_notification", "message": "New announcement"}}
            )
        
        # Broadcast announcement to course channel for real-time
        async_to_sync(channel_layer.group_send)(
            f"course_{course.id}",
            {
                "type": "course_event",
                "data": {
                    "event": "new_announcement",
                    "announcement": {
                        "id": announcement.id,
                        "title": announcement.title,
                        "content": announcement.content,
                        "user_name": self.request.user.get_full_name(),
                        "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
                    }
                }
            }
        )

    def perform_update(self, serializer):
        announcement = self.get_object()
        if not announcement.course.courseinstructors.filter(instructor=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the instructor can modify announcements")
        serializer.save()

    def perform_destroy(self, instance):
        if not instance.course.courseinstructors.filter(instructor=self.request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only the instructor can delete announcements")
        instance.delete()
