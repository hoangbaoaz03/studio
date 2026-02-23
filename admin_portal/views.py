from rest_framework.views import APIView
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from course.models import Course, Lecture
from course.serializers import CourseListSerializer, LectureSerializer
from payments.models import Transaction, InstructorPayout
from result.models import Enrollment

User = get_user_model()

class StatsOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1. User Stats
        total_users = User.objects.count()
        instructors_count = User.objects.filter(is_instructor=True).count()
        students_count = total_users - instructors_count # Simplification

        # 2. Revenue Stats
        total_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('gross_amount')
        )['total'] or 0
        
        platform_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('platform_fee')
        )['total'] or 0

        # 3. Course Stats
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(status='published').count()
        pending_courses = Course.objects.filter(status='pending').count()

        # 4. Enrollment Stats
        total_enrollments = Enrollment.objects.count()

        return Response({
            "users": {
                "total": total_users,
                "instructors": instructors_count,
                "students": students_count
            },
            "revenue": {
                "total": total_revenue,
                "platform": platform_revenue
            },
            "courses": {
                "total": total_courses,
                "published": published_courses,
                "pending": pending_courses
            },
            "enrollments": {
                "total": total_enrollments
            }
        })

class AdminCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset for managing courses (approve/reject)
    """
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        search = self.request.query_params.get('search')

        if status_param:
            queryset = queryset.filter(status=status_param)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(instructor__username__icontains=search)
            )
        
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        course = self.get_object()
        if course.status == 'published':
            return Response({'message': 'Course already published'}, status=status.HTTP_400_BAD_REQUEST)
        
        course.status = 'published'
        course.save()
        # TODO: Send notification to instructor
        return Response({'message': 'Course approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        course = self.get_object()
        reason = request.data.get('reason', 'Violation of guidelines')
        
        course.status = 'draft' # Or specific 'rejected' status if model supported
        course.save()
        # TODO: Send notification with reason
        return Response({'message': 'Course rejected'})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        course = self.get_object()
        course.is_active = not course.is_active
        course.save()
        return Response({'message': f"Course {'activated' if course.is_active else 'deactivated'}", 'is_active': course.is_active})

class AdminLectureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset for viewing and managing individual lectures (Review content)
    """
    queryset = Lecture.objects.all().order_by('-created_at')
    serializer_class = LectureSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        instructor_id = self.request.query_params.get('instructor')
        course_id = self.request.query_params.get('course')
        search = self.request.query_params.get('search')
        
        if instructor_id:
            queryset = queryset.filter(section__course__instructor_id=instructor_id)
        
        if course_id:
            queryset = queryset.filter(section__course_id=course_id)
            
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset
    
    @action(detail=True, methods=['patch'])
    def update_note(self, request, pk=None):
        lecture = self.get_object()
        note = request.data.get('admin_note')
        if note is not None:
             lecture.admin_note = note
             lecture.save()
             return Response({"status": "note updated", "admin_note": lecture.admin_note})
        return Response({"error": "No note provided"}, status=400)


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_instructor', 'is_active', 'is_staff', 'date_joined']

class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        role = self.request.query_params.get('role')

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if role == 'instructor':
            queryset = queryset.filter(is_instructor=True)
        elif role == 'student':
            queryset = queryset.filter(is_instructor=False, is_staff=False)
        elif role == 'admin':
            queryset = queryset.filter(is_staff=True)
            
        return queryset

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        # Prevent deactivating self
        if user == request.user:
            return Response({'message': 'Cannot deactivate yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = not user.is_active
        user.save()
        return Response({'message': f"User {'activated' if user.is_active else 'deactivated'}"})

    @action(detail=True, methods=['post'])
    def verify_instructor(self, request, pk=None):
        user = self.get_object()
        if not user.is_instructor:
            return Response({'message': 'User is not an instructor'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Access profile safely
        try:
            profile = user.instructor_profile
            profile.verified = True
            profile.save()
            return Response({'message': 'Instructor verified'})
            return Response({'message': 'Instructor verified'})
        except Exception:
             return Response({'message': 'Instructor profile not found'}, status=status.HTTP_404_NOT_FOUND)

class TransactionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'student_name', 'course_title',
            'gross_amount', 'platform_fee', 'instructor_revenue',
            'payment_method', 'status', 'created_at'
        ]

class PayoutSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.full_name', read_only=True)
    instructor_email = serializers.CharField(source='instructor.email', read_only=True)
    
    class Meta:
        model = InstructorPayout
        fields = [
            'id', 'instructor_name', 'instructor_email',
            'period_year', 'period_month',
            'total_revenue', 'platform_fee', 'payout_amount',
            'status', 'created_at', 'paid_at', 'payment_method'
        ]

class AdminFinanceViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        queryset = Transaction.objects.all().order_by('-created_at')
        
        # Filtering
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(student__email__icontains=search) |
                Q(course__title__icontains=search)
            )

        # Pagination (simple manual or drf)
        page = self.paginate_queryset(queryset, request)
        if page is not None:
             serializer = TransactionSerializer(page, many=True)
             return self.get_paginated_response(serializer.data)
             
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def payouts(self, request):
        queryset = InstructorPayout.objects.all().order_by('-period_year', '-period_month')
        
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        serializer = PayoutSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def process_payout(self, request, pk=None):
        try:
            payout = InstructorPayout.objects.get(pk=pk)
        except InstructorPayout.DoesNotExist:
            return Response({'error': 'Payout not found'}, status=status.HTTP_404_NOT_FOUND)
            
        new_status = request.data.get('status')
        if new_status not in ['processing', 'paid', 'failed']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
            
        payout.status = new_status
        if new_status == 'paid':
            from django.utils import timezone
            payout.paid_at = timezone.now()
            
        payout.save()
        return Response({'message': f'Payout marked as {new_status}'})

    # Helper for pagination in ViewSet (not ModelViewSet)
    def paginate_queryset(self, queryset, request):
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        self.paginator = paginator
        return paginator.paginate_queryset(queryset, request, view=self)
        
    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)

from core.models import SystemKey

class SystemKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemKey
        fields = ['id', 'key', 'value', 'type', 'description', 'updated_at']
        read_only_fields = ['id', 'updated_at']

class AdminSettingsViewSet(viewsets.ModelViewSet):
    """
    Manage system configuration
    Only Admins can modify settings.
    """
    queryset = SystemKey.objects.all().order_by('key')
    serializer_class = SystemKeySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'key'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        value = request.data.get('value')
        
        # Validation based on type
        if instance.type == 'bool':
             if str(value).lower() not in ['true', 'false']:
                 return Response({'error': 'Value must be "true" or "false"'}, status=status.HTTP_400_BAD_REQUEST)
        elif instance.type == 'int':
            try:
                int(value)
            except ValueError:
                return Response({'error': 'Value must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        elif instance.type == 'float':
            try:
                float(value)
            except ValueError:
                return Response({'error': 'Value must be a float'}, status=status.HTTP_400_BAD_REQUEST)
        elif instance.type == 'json':
            import json
            try:
                if isinstance(value, dict):
                     value = json.dumps(value)
                else:
                     json.loads(value)
            except ValueError:
                return Response({'error': 'Value must be valid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow updating value only
        instance.value = value
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['get'])
    def public_config(self, request):
        """
        Public endpoint for frontend to get allowed config (Logo, Maintenance Mode)
        This should technically be in a public ViewSet, but defined here for reference.
        Authenticaton: AllowAny (override if needed, but for now kept constrained)
        """
        # For actual public access, use a separate View in core/views.py
        qs = SystemKey.objects.filter(is_public=True)
        data = {item.key: item.cast_value for item in qs}
        return Response(data)

from rest_framework.permissions import AllowAny

class PingView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"message": "pong"})
