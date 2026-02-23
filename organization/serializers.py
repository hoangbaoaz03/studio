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
        fields = ['full_name', 'email', 'company_name', 'team_size', 'message', 'status', 'request_type']
        read_only_fields = ['status', 'created_at']
