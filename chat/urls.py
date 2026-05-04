from django.urls import path
from .views import ChatWidgetAPIView, CourseInsightsAPIView, LectureVideoInfoAPIView, SalesChatAPIView

urlpatterns = [
    path('widget/', ChatWidgetAPIView.as_view(), name='chat-widget'),
    path('sales-widget/', SalesChatAPIView.as_view(), name='sales-widget'),
    path('course-insights/', CourseInsightsAPIView.as_view(), name='course-insights'),
    path('lecture-video/<int:lecture_id>/', LectureVideoInfoAPIView.as_view(), name='lecture-video-info'),
]
