from rest_framework import serializers
from .models import Organization, OrganizationMember, Team
from accounts.serializers import UserSerializer

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'domain', 'subscription_plan', 'max_users', 'logo', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']

class TeamSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'member_count', 'created_at']

class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = OrganizationMember
        fields = ['id', 'user', 'user_details', 'role', 'team', 'team_name', 'is_active', 'date_joined']
        read_only_fields = ['date_joined']

class BusinessLeadSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import BusinessLead
        model = BusinessLead
        fields = ['id', 'full_name', 'email', 'company_name', 'team_size', 'message', 'status', 'request_type']
        read_only_fields = ['status', 'created_at']

    def validate_email(self, value):
        from .models import BusinessLead
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if BusinessLead.objects.filter(email=value).exists():
            raise serializers.ValidationError("Yêu cầu demo với email này đã được gửi trước đó.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email này đã được gắn với một tài khoản hệ thống.")
        return value

class CourseLicenseSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)
    available_seats = serializers.IntegerField(source='get_available_seats', read_only=True)

    class Meta:
        from .models import CourseLicense
        model = CourseLicense
        fields = ['id', 'course', 'course_title', 'course_thumbnail', 'seats_total', 'seats_used', 'available_seats', 'created_at']

class EmployeeCourseAccessSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        from .models import EmployeeCourseAccess
        model = EmployeeCourseAccess
        fields = ['id', 'user', 'user_email', 'user_name', 'status', 'granted_at']
