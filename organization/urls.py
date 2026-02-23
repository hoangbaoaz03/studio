from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, TeamViewSet, LeadCreateView

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'teams', TeamViewSet, basename='team')

app_name = 'organization'

urlpatterns = [
    path('', include(router.urls)),
    path('leads/', LeadCreateView.as_view(), name='lead-create'),
]
