from rest_framework.views import APIView
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from django.utils import timezone

from course.models import Course, Lecture, Category
from course.serializers import CourseListSerializer, LectureSerializer, CategorySerializer, CategoryTreeSerializer
from payments.models import Transaction, InstructorPayout, B2BPayment
from result.models import Enrollment
from organization.models import Organization
from .models import AdminPermission

User = get_user_model()

# Valid module keys for admin permissions
ADMIN_MODULE_KEYS = [
    'dashboard', 'users', 'instructor_applications', 'business_leads',
    'categories', 'courses', 'finance', 'reports', 'analytics', 'settings',
]


class IsSuperUser(IsAdminUser):
    """Only allow superusers."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


# ─────────────────────────────────────────────────────────────
# Stats Overview
# ─────────────────────────────────────────────────────────────

class StatsOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        instructors_count = User.objects.filter(is_instructor=True).count()
        students_count = total_users - instructors_count

        total_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('gross_amount')
        )['total'] or 0
        
        platform_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('platform_fee')
        )['total'] or 0

        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(status='published').count()
        pending_courses = Course.objects.filter(status='pending').count()
        total_enrollments = Enrollment.objects.count()

        return Response({
            "users": {
                "total": total_users,
                "instructors": instructors_count,
                "students": students_count
            },
            "revenue": {
                "total": float(total_revenue),
                "platform": float(platform_revenue)
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


# ─────────────────────────────────────────────────────────────
# Courses
# ─────────────────────────────────────────────────────────────

class AdminCourseViewSet(viewsets.ReadOnlyModelViewSet):
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
        return Response({'message': 'Course approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        course = self.get_object()
        reason = request.data.get('reason', 'Violation of guidelines')
        course.status = 'draft'
        course.save()
        return Response({'message': 'Course rejected'})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        course = self.get_object()
        course.is_active = not course.is_active
        course.save()
        return Response({'message': f"Course {'activated' if course.is_active else 'deactivated'}", 'is_active': course.is_active})


# ─────────────────────────────────────────────────────────────
# Lectures
# ─────────────────────────────────────────────────────────────

class AdminLectureViewSet(viewsets.ReadOnlyModelViewSet):
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


# ─────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_instructor', 'is_business', 'is_active', 'is_staff', 'date_joined']


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
            queryset = queryset.filter(is_instructor=False, is_staff=False, is_business=False)
        elif role == 'admin':
            queryset = queryset.filter(is_staff=True)
        elif role == 'business':
            queryset = queryset.filter(is_business=True)
        return queryset

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
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
        try:
            profile = user.instructor_profile
            profile.verified = True
            profile.save()
            return Response({'message': 'Instructor verified'})
        except Exception:
            return Response({'message': 'Instructor profile not found'}, status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────
# Finance — Transactions, Payouts, B2B
# ─────────────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id',
            'student_name', 'student_email', 'course_title',
            'gross_amount', 'platform_fee', 'instructor_revenue',
            'payment_method', 'payment_provider_id',
            'status', 'refund_reason', 'refunded_at',
            'created_at', 'completed_at',
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
            'status', 'created_at', 'paid_at', 'payment_method',
        ]


class AdminFinanceViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    # ── Transactions ────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        queryset = Transaction.objects.select_related('student', 'course').all().order_by('-created_at')

        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        payment_method = request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(student__email__icontains=search) |
                Q(student__full_name__icontains=search) |
                Q(course__title__icontains=search)
            )

        page = self.paginate_queryset(queryset, request)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refund_transaction(self, request, pk=None):
        try:
            txn = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response({'error': 'Giao dịch không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if txn.status == 'refunded':
            return Response({'error': 'Giao dịch đã được hoàn tiền trước đó'}, status=status.HTTP_400_BAD_REQUEST)

        if txn.status != 'completed':
            return Response({'error': 'Chỉ có thể hoàn tiền giao dịch đã hoàn thành'}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', 'Theo yêu cầu khách hàng')
        txn.status = 'refunded'
        txn.refund_reason = reason
        txn.refunded_at = timezone.now()
        txn.save()

        return Response({'message': 'Hoàn tiền thành công', 'transaction_id': txn.transaction_id})

    # ── Payouts ─────────────────────────────────────────────

    @action(detail=False, methods=['get'])
    def payouts(self, request):
        queryset = InstructorPayout.objects.select_related('instructor').all().order_by('-period_year', '-period_month')

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
            payout.paid_at = timezone.now()
        payout.save()
        return Response({'message': f'Payout marked as {new_status}'})

    # ── Pagination helpers ───────────────────────────────────

    def paginate_queryset(self, queryset, request):
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        self.paginator = paginator
        return paginator.paginate_queryset(queryset, request, view=self)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)


# ─────────────────────────────────────────────────────────────
# B2B Payments
# ─────────────────────────────────────────────────────────────

class B2BPaymentSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = B2BPayment
        fields = [
            'id', 'organization', 'organization_name', 'amount', 'plan_upgrade',
            'payment_type', 'course', 'course_title', 'seats',
            'payment_proof', 'status', 'admin_note', 'created_at', 'updated_at',
        ]


class AdminB2BPaymentViewSet(viewsets.ModelViewSet):
    queryset = B2BPayment.objects.select_related('organization', 'course').all().order_by('-created_at')
    serializer_class = B2BPaymentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        payment = self.get_object()
        if payment.status == 'approved':
            return Response({'message': 'Thanh toán đã được phê duyệt trước đó'}, status=status.HTTP_400_BAD_REQUEST)

        payment.status = 'approved'
        payment.admin_note = request.data.get('note', '')
        payment.save()

        if payment.payment_type == 'COURSE' and payment.course:
            from organization.models import CourseLicense
            license, created = CourseLicense.objects.get_or_create(
                organization=payment.organization,
                course=payment.course,
                defaults={'seats_total': payment.seats}
            )
            if not created:
                license.seats_total += payment.seats
                license.save()
            return Response({'message': f'Phê duyệt thành công. Đã cấp {payment.seats} chỗ khóa học {payment.course.title}.'})
        else:
            # Upgrade Organization Plan
            org = payment.organization
            org.subscription_plan = payment.plan_upgrade
            if payment.plan_upgrade == 'ENTERPRISE':
                org.max_users = 10000
            elif payment.plan_upgrade == 'PRO':
                org.max_users = 50
            org.is_active = True
            org.save()
            return Response({'message': f'Phê duyệt thành công. Tổ chức được nâng cấp lên {payment.plan_upgrade}.'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        payment = self.get_object()
        reason = request.data.get('reason', 'Xác minh thanh toán thất bại')
        payment.status = 'rejected'
        payment.admin_note = reason
        payment.save()
        return Response({'message': 'Đã từ chối thanh toán'})


# ─────────────────────────────────────────────────────────────
# Settings
# ─────────────────────────────────────────────────────────────

from core.models import SystemKey


class SystemKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemKey
        fields = ['id', 'key', 'value', 'type', 'description', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class AdminSettingsViewSet(viewsets.ModelViewSet):
    queryset = SystemKey.objects.all().order_by('key')
    serializer_class = SystemKeySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'key'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        value = request.data.get('value')

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

        instance.value = value
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['get'])
    def public_config(self, request):
        qs = SystemKey.objects.filter(is_public=True)
        data = {item.key: item.cast_value for item in qs}
        return Response(data)


# ─────────────────────────────────────────────────────────────
# Ping
# ─────────────────────────────────────────────────────────────

from rest_framework.permissions import AllowAny


class PingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "pong"})


# ─────────────────────────────────────────────────────────────
# Instructor Applications
# ─────────────────────────────────────────────────────────────

from accounts.models import InstructorApplication
from accounts.serializers import InstructorApplicationSerializer


class AdminInstructorApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InstructorApplication.objects.all().order_by('-created_at')
    serializer_class = InstructorApplicationSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        application = self.get_object()
        if application.status == 'approved':
            return Response({'message': 'Application already approved'}, status=status.HTTP_400_BAD_REQUEST)
        application.status = 'approved'
        application.save()
        user = application.user
        user.is_instructor = True
        user.save()
        from accounts.models import InstructorProfile
        InstructorProfile.objects.get_or_create(user=user)
        return Response({'message': 'Application approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        application = self.get_object()
        reason = request.data.get('reason', 'Does not meet requirements')
        application.status = 'rejected'
        application.admin_note = reason
        application.save()
        return Response({'message': 'Application rejected successfully'})

    @action(detail=True, methods=['post'])
    def request_update(self, request, pk=None):
        application = self.get_object()
        reason = request.data.get('reason', 'Please provide more information')
        application.status = 'needs_update'
        application.admin_note = reason
        application.save()
        return Response({'message': 'Requested more information'})


# ─────────────────────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────────────────────

class AdminCategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        roots = Category.objects.get_cached_trees()

        def serialize_tree(node):
            data = CategorySerializer(node).data
            data['children'] = [serialize_tree(child) for child in node.get_children()]
            return data

        data = [serialize_tree(root) for root in roots]
        return Response(data)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        items = request.data.get('items', [])
        for item in items:
            try:
                cat = Category.objects.get(pk=item.get('id'))
                cat.order = item.get('order', 0)
                cat.save()
            except Category.DoesNotExist:
                continue
        return Response({"message": "Categories reordered successfully"})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        category = self.get_object()
        category.is_active = not category.is_active
        category.save()
        return Response({
            'message': f"Category {'activated' if category.is_active else 'deactivated'}",
            'is_active': category.is_active,
        })

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        categories_to_check = category.get_descendants(include_self=True)
        courses = Course.objects.filter(category__in=categories_to_check)
        if courses.exists():
            return Response({
                "error": "Cannot delete category with existing courses.",
                "courses_count": courses.count(),
                "requires_move": True,
            }, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def move_courses(self, request, pk=None):
        category = self.get_object()
        target_id = request.data.get('target_category_id')
        if not target_id:
            return Response({"error": "Target category ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_category = Category.objects.get(pk=target_id)
        except Category.DoesNotExist:
            return Response({"error": "Target category not found"}, status=status.HTTP_404_NOT_FOUND)
        if target_category == category or target_category in category.get_descendants():
            return Response({"error": "Cannot move to itself or its descendants"}, status=status.HTTP_400_BAD_REQUEST)
        categories_to_move = category.get_descendants(include_self=True)
        courses = Course.objects.filter(category__in=categories_to_move)
        count = courses.update(category=target_category)
        return Response({"message": f"Successfully moved {count} courses to {target_category.name}"})


# ─────────────────────────────────────────────────────────────
# Business Leads
# ─────────────────────────────────────────────────────────────

from organization.models import BusinessLead, Organization, OrganizationMember
from django.core.mail import send_mail
from django.utils.crypto import get_random_string

class AdminBusinessLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessLead
        fields = '__all__'


class AdminBusinessLeadViewSet(viewsets.ModelViewSet):
    queryset = BusinessLead.objects.all().order_by('-created_at')
    serializer_class = AdminBusinessLeadSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        lead = self.get_object()
        if lead.status in ['APPROVED', 'CONVERTED']:
            return Response({'message': 'Lead already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Create User
        password = get_random_string(length=12)
        email = lead.email
        
        user, created = User.objects.get_or_create(email=email, defaults={
            'username': email.split('@')[0] + '_' + get_random_string(4),
            'first_name': lead.full_name,
            'is_business': True
        })
        
        if created:
            user.set_password(password)
        else:
            user.is_business = True
            password = "Đã có tài khoản từ trước (Dùng mật khẩu cũ)"
        user.save()
        
        # 2. Create Organization
        org, org_created = Organization.objects.get_or_create(
            name=lead.company_name,
            defaults={'max_users': 50}
        )
        
        # 3. Add User to Org
        OrganizationMember.objects.get_or_create(
            organization=org,
            user=user,
            defaults={'role': 'OWNER'}
        )
        
        # 4. Update Lead
        lead.status = 'CONVERTED'
        lead.save()
        
        # 5. Send Email
        try:
            send_mail(
                subject='Your Studigo Business Account',
                message=f'Hello {lead.full_name},\n\nYour Studigo Business account has been created.\n\nLogin URL: http://localhost:3000/login\nUsername: {user.username}\nPassword: {password}\n\nWelcome to Studigo Business!',
                from_email='no-reply@studigo.com',
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            
        return Response({
            'message': 'Lead accepted, Business account provisioned, and email sent.',
            'email': email,
            'username': user.username,
            'password': password
        })


# ─────────────────────────────────────────────────────────────
# Admin Permissions Management
# ─────────────────────────────────────────────────────────────

class MyAdminPermissionsView(APIView):
    """Return the current user's allowed admin modules."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        if request.user.is_superuser:
            return Response({
                "is_superuser": True,
                "allowed_modules": ADMIN_MODULE_KEYS + ['admin_users'],
            })

        perm = AdminPermission.objects.filter(user=request.user).first()
        return Response({
            "is_superuser": False,
            "allowed_modules": perm.allowed_modules if perm else ['dashboard'],
        })


class AdminUsersListView(APIView):
    """List all staff users and their permissions. Superuser only."""
    permission_classes = [IsSuperUser]

    def get(self, request):
        search = request.query_params.get('search', '')
        staff_users = User.objects.filter(is_staff=True).order_by('-date_joined')

        data = []
        for u in staff_users:
            perm = AdminPermission.objects.filter(user=u).first()
            data.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.get_full_name() or u.username,
                "is_superuser": u.is_superuser,
                "is_staff": u.is_staff,
                "allowed_modules": perm.allowed_modules if perm else [],
                "date_joined": u.date_joined,
            })

        return Response({
            "users": data,
            "available_modules": ADMIN_MODULE_KEYS,
        })


class SetUserStaffView(APIView):
    """Toggle is_staff for a user. Superuser only."""
    permission_classes = [IsSuperUser]

    def post(self, request):
        email = request.data.get('email', '').strip()
        make_staff = request.data.get('is_staff', True)

        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": f"User '{email}' not found"}, status=status.HTTP_404_NOT_FOUND)

        if target_user.is_superuser:
            return Response({"detail": "Cannot modify a superuser"}, status=status.HTTP_400_BAD_REQUEST)

        target_user.is_staff = make_staff
        target_user.save()

        # Create default permissions if making staff
        if make_staff:
            AdminPermission.objects.get_or_create(
                user=target_user,
                defaults={"allowed_modules": ["dashboard"]}
            )
        else:
            # Remove permissions when revoking staff
            AdminPermission.objects.filter(user=target_user).delete()

        return Response({
            "detail": f"User '{target_user.username}' is now {'staff' if make_staff else 'not staff'}",
            "id": target_user.id,
            "is_staff": target_user.is_staff,
        })


class UpdateAdminPermissionsView(APIView):
    """Update allowed modules for a staff user. Superuser only."""
    permission_classes = [IsSuperUser]

    def put(self, request, user_id):
        target_user = User.objects.filter(id=user_id, is_staff=True).first()
        if not target_user:
            return Response({"detail": "Staff user not found"}, status=status.HTTP_404_NOT_FOUND)

        if target_user.is_superuser:
            return Response({"detail": "Cannot modify superuser permissions"}, status=status.HTTP_400_BAD_REQUEST)

        modules = request.data.get('allowed_modules', [])
        # Validate module keys
        valid_modules = [m for m in modules if m in ADMIN_MODULE_KEYS]

        perm, created = AdminPermission.objects.get_or_create(
            user=target_user,
            defaults={"allowed_modules": valid_modules}
        )
        if not created:
            perm.allowed_modules = valid_modules
            perm.save()

        return Response({
            "id": target_user.id,
            "allowed_modules": perm.allowed_modules,
            "detail": "Permissions updated"
        })
