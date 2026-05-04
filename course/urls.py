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
router.register(r'announcements', views.AnnouncementViewSet, basename='announcement')

from django.http import JsonResponse
def fix_db(request):
    from .models import Course, CourseInstructor
    from accounts.models import User
    
    first_instructor = User.objects.filter(is_instructor=True).first()
    if not first_instructor:
        return JsonResponse({"error": "No instructor found to assign courses to."})
        
    all_courses = Course.objects.all()
    count = 0
    for course in all_courses:
        obj, created = CourseInstructor.objects.get_or_create(
            course=course,
            instructor=first_instructor,
            defaults={'is_primary': True}
        )
        if created:
            count += 1
        
    return JsonResponse({"status": "success", "assigned_to_instructor": count, "instructor": first_instructor.username})

urlpatterns = [
    path('fix-db/', fix_db),
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
