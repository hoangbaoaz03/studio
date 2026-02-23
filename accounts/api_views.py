from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer

class UserRegistrationAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class MeAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
