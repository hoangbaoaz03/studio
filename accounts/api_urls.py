from django.urls import path
from .api_views import UserRegistrationAPIView, MeAPIView

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('me/', MeAPIView.as_view(), name='me'),
]
