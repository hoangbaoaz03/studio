"""
Main URL configuration for marketplace platform
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from accounts.api_views import CustomTokenObtainPairView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

admin.site.site_header = "Studigo Marketplace Admin"
admin.site.site_title = "Studigo Admin"

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # JWT Authentication
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OAuth / Social Auth
    path('accounts/', include('allauth.urls')),
    
    # API Endpoints
    path('api/courses/', include('course.urls', namespace='course')),
    path('api/learning/', include('result.urls', namespace='result')),
    path('api/payments/', include('payments.urls', namespace='payments')),
    path('api/instructor/', include('accounts.instructor_urls', namespace='instructor')),
    path('api/certification/', include('certification.urls', namespace='certification')),
    path('api/business/', include('organization.urls', namespace='organization')),
    path('api/auth/', include('accounts.api_urls')),
    path('api/admin/', include('admin_portal.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/', include('core.urls', namespace='core')),  # Homepage & discovery (Keep last)
]

from django.urls import re_path
from core.video_serve import serve_video_with_range

# Media files (development only)
if settings.DEBUG:
    # Serve MP4 files with our custom range-response view
    urlpatterns += [
        re_path(r'^media/(?P<path>.*\.mp4)$', serve_video_with_range),
    ]
    # Serve other media files normally
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
