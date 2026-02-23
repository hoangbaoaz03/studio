from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StatsOverviewView, AdminCourseViewSet, AdminUserViewSet, AdminFinanceViewSet, AdminSettingsViewSet, PingView, AdminLectureViewSet
from reports.views import ReportViewSet
from analytics.views import AnalyticsViewSet

router = DefaultRouter()
router.register(r'courses', AdminCourseViewSet, basename='admin-course')
router.register(r'lectures', AdminLectureViewSet, basename='admin-lecture')
router.register(r'users', AdminUserViewSet, basename='admin-user')
router.register(r'finance', AdminFinanceViewSet, basename='admin-finance')
router.register(r'settings', AdminSettingsViewSet, basename='admin-settings')
router.register(r'reports', ReportViewSet, basename='admin-report')
router.register(r'analytics', AnalyticsViewSet, basename='admin-analytics')

urlpatterns = [
    path('ping/', PingView.as_view(), name='admin-ping'),
    path('stats/overview/', StatsOverviewView.as_view(), name='admin-stats-overview'),
    path('', include(router.urls)),
]
