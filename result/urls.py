"""
URL routing for Enrollment and Review API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, student_api

app_name = 'result'

router = DefaultRouter()
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'answers', views.AnswerViewSet, basename='answer')
router.register(r'wishlist', views.WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
    
    # Student dashboard
    path('my-learning/', student_api.my_learning, name='my-learning'),
    path('my-stats/', student_api.my_progress_stats, name='my-stats'),
    path('my-certificates/', student_api.my_certificates, name='my-certificates'),
    path('my-wishlist/', student_api.my_wishlist, name='my-wishlist'),
    path('player/<slug:course_slug>/', student_api.course_player_data, name='course-player'),
    path('quiz/<int:lecture_id>/', student_api.get_quiz_data, name='quiz-data'),
    path('quiz/<int:lecture_id>/submit/', student_api.submit_quiz_answers, name='quiz-submit'),
    path('certificate/<int:enrollment_id>/generate/', student_api.generate_certificate, name='generate-certificate'),
    
    # Learning Progress & Notes
    path('lecture/<int:lecture_id>/complete/', student_api.update_lecture_progress, name='complete-lecture'),
    path('notes/', student_api.save_note, name='save-note'),
    path('course/<slug:course_slug>/notes/', student_api.get_notes, name='get-notes'),
]
