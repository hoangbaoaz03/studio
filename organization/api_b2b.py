from rest_framework import views, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Sum

from .models import Organization, CourseLicense, EmployeeCourseAccess, OrganizationMember, Team, TeamCoursePermission
from payments.models import Order, OrderItem
from course.models import Course
from result.models import Enrollment, LectureProgress, QuizResult
from django.contrib.auth import get_user_model

def get_user_org_any(user):
    """Get org for any member (including MANAGER)"""
    member = OrganizationMember.objects.filter(user=user, role__in=['OWNER', 'ADMIN', 'MANAGER']).first()
    if member:
        return member.organization, member
    return None, None

def get_user_org(user):
    member = OrganizationMember.objects.filter(user=user, role__in=['OWNER', 'ADMIN']).first()
    if member:
        return member.organization
    return None

class B2BBulkOrderView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response({"detail": "Not authorized as org admin"}, status=status.HTTP_403_FORBIDDEN)
            
        course_id = request.data.get('course_id')
        seats = int(request.data.get('seats', 0))
        company_name = request.data.get('company_name', '')
        tax_code = request.data.get('tax_code', '')
        company_address = request.data.get('company_address', '')
        
        if seats <= 0 or not course_id:
            return Response({"detail": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
            
        course = get_object_or_404(Course, id=course_id)
        
        # Calculate discount based on user request
        discount_percent = 0
        if seats >= 100:
            discount_percent = 30
        elif seats >= 50:
            discount_percent = 20
        elif seats >= 10:
            discount_percent = 10
        else:
            discount_percent = 0
            
        original_price = float(course.price) * seats
        discount_amount = original_price * (discount_percent / 100.0)
        final_amount = original_price - discount_amount
        
        # Mock PDF URL
        invoice_pdf_url = f"https://mock-invoice-service.com/invoice/B2B-{org.id}-{timezone.now().timestamp()}.pdf"
        
        from payments.models import B2BPayment
        
        payment = B2BPayment.objects.create(
            organization=org,
            payment_type='COURSE',
            course=course,
            seats=seats,
            amount=final_amount,
            status='pending'
        )
        
        return Response({
            "message": "Payment request sent to system admin for approval.",
            "payment_id": payment.id,
            "invoice_pdf_url": invoice_pdf_url,
            "final_amount": final_amount,
            "discount_percent": discount_percent
        })

class B2BLicenseViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response([])
        licenses = CourseLicense.objects.filter(organization=org).select_related('course')
        data = []
        for lic in licenses:
            data.append({
                "id": lic.id,
                "course_id": lic.course.id,
                "course_title": lic.course.title,
                "course_image": lic.course.thumbnail.url if lic.course.thumbnail else None,
                "seats_total": lic.seats_total,
                "seats_used": lic.seats_used,
                "available": lic.get_available_seats(),
                "created_at": lic.created_at
            })
        return Response(data)
        
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        # Allow both Admin and Manager (with TeamCoursePermission)
        org = get_user_org(request.user)
        if not org:
            org_any, member = get_user_org_any(request.user)
            if not org_any or not member or member.role != 'MANAGER':
                return Response({"detail": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)
            # Check if manager has permission for this license
            has_perm = TeamCoursePermission.objects.filter(
                team=member.team, course_license_id=pk
            ).exists()
            if not has_perm:
                return Response({"detail": "Bạn chưa được cấp quyền quản lý khóa học này."}, status=status.HTTP_403_FORBIDDEN)
            org = org_any
        
        lic = get_object_or_404(CourseLicense, id=pk, organization=org)
        email = request.data.get('email')
        
        if not email:
            return Response({"detail": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        User = get_user_model()
        target_user = User.objects.filter(email=email).first()
        if not target_user:
            return Response({"detail": f"Người dùng với email '{email}' không tồn tại trên hệ thống. Vui lòng yêu cầu nhân viên tạo tài khoản trước."}, status=status.HTTP_404_NOT_FOUND)
        
        if lic.get_available_seats() <= 0:
            return Response({"detail": "Đã hết số lượng chỗ (seats) cho khóa học này."}, status=status.HTTP_400_BAD_REQUEST)
            
        access, created = EmployeeCourseAccess.objects.get_or_create(
            course_license=lic,
            user=target_user,
            defaults={'organization': org, 'granted_by': request.user, 'status': 'active'}
        )
        
        if not created and access.status == 'active':
            return Response({"detail": "Người dùng này đã được gán vào khóa học."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not created and access.status == 'revoked':
            access.status = 'active'
            access.granted_by = request.user
            access.save()
            lic.seats_used += 1
            lic.save()
        elif created:
            lic.seats_used += 1
            lic.save()
            
        # Add to organization if not already a member
        OrganizationMember.objects.get_or_create(
            organization=org,
            user=target_user,
            defaults={'role': 'LEARNER'}
        )
        
        # Create or update Enrollment
        enrollment, _ = Enrollment.objects.get_or_create(
            student=target_user,
            course=lic.course,
            defaults={'organization': org}
        )
        
        # Ensure enrollment is linked to org even if it existed before
        if enrollment.organization != org:
            enrollment.organization = org
            enrollment.save()
            
        return Response({"detail": "Đã gán tài khoản thành công", "seats_used": lic.seats_used})

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        org = get_user_org(request.user)
        lic = get_object_or_404(CourseLicense, id=pk, organization=org)
        user_id = request.data.get('user_id')
        access = get_object_or_404(EmployeeCourseAccess, course_license=lic, user_id=user_id)
        
        if access.status == 'active':
            access.status = 'revoked'
            access.revoked_at = timezone.now()
            access.save()
            
            # User request: "Revoke User -> KHONG xoa". So we keep Enrollment intact.
            
            if lic.seats_used > 0:
                lic.seats_used -= 1
                lic.save()
            
        return Response({"detail": "Seat revoked", "seats_used": lic.seats_used})
        
    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        org = get_user_org(request.user)
        lic = get_object_or_404(CourseLicense, id=pk, organization=org)
        accesses = EmployeeCourseAccess.objects.filter(course_license=lic)
        data = []
        for acc in accesses:
            data.append({
                "id": acc.id,
                "user_id": acc.user.id,
                "user_name": acc.user.get_full_name() or acc.user.username,
                "email": acc.user.email,
                "status": acc.status,
                "granted_at": acc.granted_at
            })
        return Response(data)

class B2BAnalyticsView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response({})
        
        # Get all user IDs belonging to this org
        org_user_ids = OrganizationMember.objects.filter(
            organization=org
        ).values_list('user_id', flat=True)
        
        # Overall Progress - enrollments of org members
        enrollments = Enrollment.objects.filter(student_id__in=org_user_ids)
        avg_progress = enrollments.aggregate(Avg('progress_percent'))['progress_percent__avg'] or 0
        
        # Total watched time - lecture progress of org members
        progresses = LectureProgress.objects.filter(enrollment__student_id__in=org_user_ids)
        total_watched = progresses.aggregate(Sum('watched_seconds'))['watched_seconds__sum'] or 0
        
        # Quiz scores
        avg_score = QuizResult.objects.filter(student_id__in=org_user_ids).aggregate(Avg('score_achieved'))['score_achieved__avg'] or 0
        
        # Active learners - org members who have at least 1 lecture progress
        active_learners = progresses.values('enrollment__student').distinct().count()
        
        # Top learners
        top_learners = []
        for enr in enrollments.select_related('student', 'course').order_by('-progress_percent')[:5]:
            top_learners.append({
                "name": enr.student.get_full_name() or enr.student.username,
                "course": enr.course.title,
                "progress": enr.progress_percent
            })
            
        return Response({
            "avg_progress_percent": round(avg_progress, 2),
            "total_watched_seconds": total_watched,
            "avg_quiz_score": round(avg_score, 2),
            "active_learners": active_learners,
            "top_learners": top_learners
        })

class B2BLearnersProgressView(views.APIView):
    """
    Detailed progress for each learner in the organization.
    Supports filtering by course, team, and search.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response([])
            
        course_id = request.query_params.get('course_id')
        team_id = request.query_params.get('team_id')
        search = request.query_params.get('search')
        
        # Base query: All enrollments belonging to learners in this org
        from django.db.models import Q
        
        enrollments = Enrollment.objects.filter(
            student__organization_memberships__organization=org
        ).select_related('student', 'course')
        
        if course_id:
            enrollments = enrollments.filter(course_id=course_id)
            
        if team_id:
            enrollments = enrollments.filter(student__organization_memberships__team_id=team_id)
            
        if search:
            enrollments = enrollments.filter(
                Q(student__first_name__icontains=search) | 
                Q(student__last_name__icontains=search) |
                Q(student__email__icontains=search) |
                Q(student__username__icontains=search)
            )
            
        enrollments = enrollments.distinct()
        
        data = []
        for enr in enrollments:
            member = OrganizationMember.objects.filter(user=enr.student, organization=org).first()
            team_name = member.team.name if member and member.team else "N/A"
            
            # Avg quiz score for this course
            quiz_avg = QuizResult.objects.filter(student=enr.student, quiz__section__course=enr.course).aggregate(Avg('score_achieved'))['score_achieved__avg']
            
            data.append({
                "id": enr.id,
                "student_name": enr.student.get_full_name() or enr.student.username,
                "student_email": enr.student.email,
                "course_title": enr.course.title,
                "team_name": team_name,
                "progress_percent": enr.progress_percent,
                "quiz_avg": round(quiz_avg, 2) if quiz_avg else 0,
                "last_accessed": enr.last_accessed,
                "completed": bool(enr.completed_at)
            })
            
        return Response(data)


class B2BMembersView(views.APIView):
    """List all members of the current user's organization."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response([])

        search = request.query_params.get('search', '')
        members = OrganizationMember.objects.filter(
            organization=org
        ).select_related('user', 'team')

        if search:
            from django.db.models import Q
            members = members.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search)
            )

        data = []
        for m in members:
            data.append({
                "id": m.id,
                "user_id": m.user.id,
                "name": m.user.get_full_name() or m.user.username,
                "email": m.user.email,
                "role": m.role,
                "team": m.team.name if m.team else "Unassigned",
                "team_id": m.team.id if m.team else None,
                "is_active": m.is_active,
                "date_joined": m.date_joined,
            })
        return Response(data)


class B2BTeamsView(views.APIView):
    """List all teams or create a new team."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response([])

        teams = Team.objects.filter(organization=org)
        data = []
        for t in teams:
            member_count = OrganizationMember.objects.filter(organization=org, team=t).count()
            manager = OrganizationMember.objects.filter(organization=org, team=t, role__in=['OWNER', 'ADMIN', 'MANAGER']).select_related('user').first()
            data.append({
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "members": member_count,
                "manager": manager.user.get_full_name() or manager.user.username if manager else "Unassigned",
            })
        return Response(data)

    def post(self, request):
        org = get_user_org(request.user)
        if not org:
            return Response({"detail": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)

        name = request.data.get('name', '').strip()
        description = request.data.get('description', '').strip()

        if not name:
            return Response({"detail": "Tên phòng ban không được để trống"}, status=status.HTTP_400_BAD_REQUEST)

        if Team.objects.filter(organization=org, name=name).exists():
            return Response({"detail": "Phòng ban đã tồn tại"}, status=status.HTTP_400_BAD_REQUEST)

        team = Team.objects.create(organization=org, name=name, description=description)
        return Response({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "members": 0,
            "manager": "Unassigned",
        }, status=status.HTTP_201_CREATED)


class B2BMemberUpdateView(views.APIView):
    """Update a member's role and/or team assignment."""
    permission_classes = [IsAuthenticated]

    def put(self, request, member_id):
        org = get_user_org(request.user)
        if not org:
            return Response({"detail": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)

        member = get_object_or_404(OrganizationMember, id=member_id, organization=org)

        new_role = request.data.get('role')
        new_team_id = request.data.get('team_id')

        if new_role and new_role in dict(OrganizationMember.ROLE_CHOICES):
            # Don't allow changing OWNER role
            if member.role == 'OWNER' and new_role != 'OWNER':
                return Response({"detail": "Không thể thay đổi vai trò của Owner"}, status=status.HTTP_400_BAD_REQUEST)
            member.role = new_role

        if new_team_id is not None:
            if new_team_id == '' or new_team_id == 0:
                member.team = None
            else:
                team = get_object_or_404(Team, id=new_team_id, organization=org)
                member.team = team

        member.save()

        return Response({
            "id": member.id,
            "role": member.role,
            "team": member.team.name if member.team else "Unassigned",
            "detail": "Cập nhật thành công"
        })


class B2BTeamPermissionsView(views.APIView):
    """Manage course license permissions for a team."""
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        org = get_user_org(request.user)
        if not org:
            return Response({"detail": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)

        team = get_object_or_404(Team, id=team_id, organization=org)
        perms = TeamCoursePermission.objects.filter(team=team).select_related('course_license__course', 'granted_by')

        data = []
        for p in perms:
            data.append({
                "id": p.id,
                "license_id": p.course_license.id,
                "course_title": p.course_license.course.title,
                "seats_total": p.course_license.seats_total,
                "seats_used": p.course_license.seats_used,
                "granted_by": p.granted_by.get_full_name() or p.granted_by.username if p.granted_by else "N/A",
                "created_at": p.created_at,
            })
        return Response(data)

    def post(self, request, team_id):
        org = get_user_org(request.user)
        if not org:
            return Response({"detail": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)

        team = get_object_or_404(Team, id=team_id, organization=org)
        license_id = request.data.get('license_id')

        if not license_id:
            return Response({"detail": "license_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        lic = get_object_or_404(CourseLicense, id=license_id, organization=org)

        perm, created = TeamCoursePermission.objects.get_or_create(
            team=team,
            course_license=lic,
            defaults={'granted_by': request.user}
        )

        if not created:
            return Response({"detail": "Quyền đã tồn tại"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "id": perm.id,
            "license_id": lic.id,
            "course_title": lic.course.title,
            "detail": "Đã cấp quyền thành công"
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, team_id):
        org = get_user_org(request.user)
        if not org:
            return Response({"detail": "Không có quyền"}, status=status.HTTP_403_FORBIDDEN)

        perm_id = request.data.get('permission_id')
        if not perm_id:
            return Response({"detail": "permission_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        perm = get_object_or_404(TeamCoursePermission, id=perm_id, team__organization=org)
        perm.delete()
        return Response({"detail": "Đã thu hồi quyền"})
