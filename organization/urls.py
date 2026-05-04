from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, TeamViewSet, LeadCreateView
from .api_b2b import B2BBulkOrderView, B2BLicenseViewSet, B2BAnalyticsView, B2BLearnersProgressView, B2BMembersView, B2BTeamsView, B2BMemberUpdateView, B2BTeamPermissionsView

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'b2b/licenses', B2BLicenseViewSet, basename='b2b-licenses')

app_name = 'organization'

urlpatterns = [
    path('', include(router.urls)),
    path('leads/', LeadCreateView.as_view(), name='lead-create'),
    path('b2b/bulk-order/', B2BBulkOrderView.as_view(), name='b2b-bulk-order'),
    path('b2b/analytics/', B2BAnalyticsView.as_view(), name='b2b-analytics'),
    path('b2b/learners-progress/', B2BLearnersProgressView.as_view(), name='b2b-learners-progress'),
    path('b2b/members/', B2BMembersView.as_view(), name='b2b-members'),
    path('b2b/members/<int:member_id>/update-role/', B2BMemberUpdateView.as_view(), name='b2b-member-update'),
    path('b2b/teams-list/', B2BTeamsView.as_view(), name='b2b-teams-list'),
    path('b2b/teams/<int:team_id>/permissions/', B2BTeamPermissionsView.as_view(), name='b2b-team-permissions'),
]
