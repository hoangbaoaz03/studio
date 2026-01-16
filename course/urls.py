"""
URL routing for Course API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, course_wizard, video_service, player_api

app_name = 'course'

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'subcategories', views.SubcategoryViewSet, basename='subcategory')
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'sections', views.SectionViewSet, basename='section')
router.register(r'lectures', views.LectureViewSet, basename='lecture')

urlpatterns = [
    path('', include(router.urls)),
    
    # Course creation wizard
    path('wizard/create/', course_wizard.create_course_step1, name='wizard-create'),
    path('wizard/<int:course_id>/details/', course_wizard.update_course_details, name='wizard-details'),
    path('wizard/<int:course_id>/section/', course_wizard.add_course_section, name='wizard-section'),
    path('wizard/section/<int:section_id>/lecture/', course_wizard.add_lecture, name='wizard-lecture'),
    path('wizard/<int:course_id>/pricing/', course_wizard.update_course_pricing, name='wizard-pricing'),
    path('wizard/<int:course_id>/publish/', course_wizard.publish_course, name='wizard-publish'),
    
    # Video upload
    path('video/upload-url/', video_service.generate_upload_url, name='video-upload-url'),
    path('video/attach/', video_service.attach_video_to_lecture, name='video-attach'),
    path('video/upload-local/', video_service.upload_video_local, name='video-upload-local'),
    path('video/delete/<int:lecture_id>/', video_service.delete_video, name='video-delete'),
    
    # Video player
    path('player/lecture/<int:lecture_id>/stream/', player_api.get_video_stream_url, name='player-stream'),
    path('player/lecture/<int:lecture_id>/progress/', player_api.update_playback_progress, name='player-progress'),
    path('player/lecture/<int:lecture_id>/next/', player_api.get_next_lecture, name='player-next'),
    path('player/lecture/<int:lecture_id>/resources/', player_api.get_lecture_resources, name='player-resources'),
    path('player/lecture/<int:lecture_id>/subtitles/', player_api.get_video_subtitles, name='player-subtitles'),
]
