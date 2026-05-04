from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StatsOverviewView, AdminCourseViewSet, AdminUserViewSet, AdminFinanceViewSet, 
    AdminSettingsViewSet, PingView, AdminLectureViewSet, AdminInstructorApplicationViewSet, 
    AdminB2BPaymentViewSet, AdminCategoryViewSet, AdminBusinessLeadViewSet,
    MyAdminPermissionsView, AdminUsersListView, SetUserStaffView, UpdateAdminPermissionsView
)
from reports.views import ReportViewSet
from analytics.views import AnalyticsViewSet

router = DefaultRouter()
router.register(r'categories', AdminCategoryViewSet, basename='admin-category')
router.register(r'courses', AdminCourseViewSet, basename='admin-course')
router.register(r'lectures', AdminLectureViewSet, basename='admin-lecture')
router.register(r'users', AdminUserViewSet, basename='admin-user')
router.register(r'instructor-applications', AdminInstructorApplicationViewSet, basename='admin-instructor-application')
router.register(r'finance', AdminFinanceViewSet, basename='admin-finance')
router.register(r'b2b-payments', AdminB2BPaymentViewSet, basename='admin-b2b-payment')
router.register(r'settings', AdminSettingsViewSet, basename='admin-settings')
router.register(r'reports', ReportViewSet, basename='admin-report')
router.register(r'analytics', AnalyticsViewSet, basename='admin-analytics')
router.register(r'business-leads', AdminBusinessLeadViewSet, basename='admin-business-lead')

urlpatterns = [
    path('ping/', PingView.as_view(), name='admin-ping'),
    path('stats/overview/', StatsOverviewView.as_view(), name='admin-stats-overview'),
    path('permissions/my/', MyAdminPermissionsView.as_view(), name='admin-my-permissions'),
    path('permissions/', AdminUsersListView.as_view(), name='admin-users-list'),
    path('permissions/set-staff/', SetUserStaffView.as_view(), name='admin-set-staff'),
    path('permissions/<int:user_id>/', UpdateAdminPermissionsView.as_view(), name='admin-update-permissions'),
    path('', include(router.urls)),
]

