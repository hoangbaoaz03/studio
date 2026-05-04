from django.urls import path
from .api_views import UserRegistrationAPIView, MeAPIView, GoogleLoginAPIView, FacebookLoginAPIView, InstructorApplicationAPIView, ChangePasswordAPIView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('me/', MeAPIView.as_view(), name='me'),
    path('google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('facebook/', FacebookLoginAPIView.as_view(), name='facebook_login'),
    path('instructor-application/', InstructorApplicationAPIView.as_view(), name='instructor_application'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
]
