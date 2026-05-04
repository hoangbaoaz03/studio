from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, InstructorApplication
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    ChangePasswordSerializer,
    InstructorApplicationSerializer,
    CustomTokenObtainPairSerializer
)
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class MeAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("token")
        if not access_token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify Google access token by fetching user info
        try:
            google_response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
        except requests.RequestException as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Google API request failed: {e}")
            return Response({"error": "Failed to verify Google token"}, status=status.HTTP_502_BAD_GATEWAY)

        if google_response.status_code != 200:
            return Response(
                {"error": "Invalid Google token", "detail": google_response.text},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_info = google_response.json()
        email = user_info.get("email")
        first_name = user_info.get("given_name", "")
        last_name = user_info.get("family_name", "")
        picture = user_info.get("picture", "")

        if not email:
            return Response({"error": "Email not found in Google token"}, status=status.HTTP_400_BAD_REQUEST)

        # Check or create user — use email as username for social logins
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "password": make_password(get_random_string(32)),
                "email_verified": user_info.get("email_verified", False),
            },
        )

        # Update name if user existed but had empty name fields
        if not created:
            updated = False
            if not user.first_name and first_name:
                user.first_name = first_name
                updated = True
            if not user.last_name and last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save(update_fields=["first_name", "last_name"])

        # Generate JWT Tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class FacebookLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("token")
        if not access_token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Verify Facebook Token
        try:
            fb_response = requests.get(
                "https://graph.facebook.com/me",
                params={
                    "access_token": access_token,
                    "fields": "id,name,email,first_name,last_name",
                },
                timeout=10,
            )
        except requests.RequestException as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Facebook API request failed: {e}")
            return Response({"error": "Failed to verify Facebook token"}, status=status.HTTP_502_BAD_GATEWAY)

        if fb_response.status_code != 200:
            return Response(
                {"error": "Invalid Facebook token", "detail": fb_response.text},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_info = fb_response.json()
        email = user_info.get("email")
        
        if not email:
            # Facebook might not return an email if the user didn't allow it, use id as fallback
            email = f"{user_info.get('id')}@facebook.com"

        first_name = user_info.get("first_name", "")
        last_name = user_info.get("last_name", "")

        # Check or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "password": make_password(get_random_string(32)),
                "email_verified": True,
            },
        )

        # Update name if user existed but had empty name fields
        if not created:
            updated = False
            if not user.first_name and first_name:
                user.first_name = first_name
                updated = True
            if not user.last_name and last_name:
                user.last_name = last_name
                updated = True
            if updated:
                user.save(update_fields=["first_name", "last_name"])

        # Generate JWT Tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class ChangePasswordAPIView(APIView):
    """
    Allows authenticated users to change their password.
    Returns new JWT tokens so the user stays logged in.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Verify old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": ["Mật khẩu hiện tại không đúng."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set and save the new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Generate new tokens (old tokens are invalidated by password change)
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Đổi mật khẩu thành công!",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


from .models import InstructorApplication
from .serializers import InstructorApplicationSerializer

class InstructorApplicationAPIView(APIView):
    """
    API view for users to submit and view their instructor application
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        application = InstructorApplication.objects.filter(user=request.user).order_by('-created_at').first()
        if not application:
            return Response({"detail": "No application found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = InstructorApplicationSerializer(application)
        return Response(serializer.data)

    def post(self, request):
        # Check if there is already a pending or approved application
        existing_application = InstructorApplication.objects.filter(
            user=request.user, 
            status__in=['pending', 'approved']
        ).first()
        
        if existing_application:
            return Response(
                {"error": f"You already have an application with status: {existing_application.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = InstructorApplicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, status='pending')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        # Allow updating if status is needs_update or rejected
        application = InstructorApplication.objects.filter(
            user=request.user, 
            status__in=['needs_update', 'rejected']
        ).order_by('-created_at').first()
        
        if not application:
            return Response({"error": "No application available for update."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = InstructorApplicationSerializer(application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status='pending') # Resubmit resets status to pending
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
