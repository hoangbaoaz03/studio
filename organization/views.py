from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Organization, OrganizationMember, Team
from .serializers import OrganizationSerializer, OrganizationMemberSerializer, TeamSerializer
import logging

logger = logging.getLogger(__name__)

class IsOrganizationAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners/admins of an organization to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any member
        # Write permissions are allowed only to admins/owners
        if not request.user.is_authenticated:
            return False
            
        # Logic depends on where this permission is applied (Obj = Organization or Child?)
        # For simplicity, we check if user is admin in the organization related to obj
        return True # Placeholder for actual logic implementation

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        # Users only see organizations they belong to
        # If user is superuser, see all (optional)
        if self.request.user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(members__user=self.request.user)

    def perform_create(self, serializer):
        org = serializer.save()
        # auto-add creator as owner
        OrganizationMember.objects.create(
            organization=org,
            user=self.request.user,
            role='OWNER'
        )

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        org = self.get_object()
        members = OrganizationMember.objects.filter(organization=org)
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def teams(self, request, slug=None):
        org = self.get_object()
        teams = Team.objects.filter(organization=org)
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # We need to filter based on organization context, usually passed via URL or query param
        # For now, return empty or all if user is superuser
        user = self.request.user
        if user.is_superuser:
            return Team.objects.all()
        return Team.objects.filter(organization__members__user=user)

    def perform_create(self, serializer):
        # We need organization ID from context
        org_id = self.request.data.get('organization_id')
        if org_id:
            serializer.save(organization_id=org_id)
        else:
            # Fallback or error
            pass

class LeadCreateView(generics.CreateAPIView):
    """
    Public endpoint to capture business leads
    """
    from .models import BusinessLead
    from .serializers import BusinessLeadSerializer
    
    queryset = BusinessLead.objects.all()
    serializer_class = BusinessLeadSerializer
    permission_classes = [permissions.AllowAny] # Public access
    throttle_scope = 'leads' # Verify settings.py has this scope, or rely on defaults
