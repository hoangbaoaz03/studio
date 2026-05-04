"""
DRF Serializers for User and Instructor API
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q
from .models import User, InstructorProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get(self.username_field)
        if username:
            user = User.objects.filter(Q(email=username) | Q(username=username)).first()
            if user:
                attrs[self.username_field] = user.username
        return super().validate(attrs)



class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'profile_photo',
            'bio',
            'headline',
            'website',
            'linkedin',
            'twitter',
            'youtube',
            'is_instructor',
            'is_business',
            'is_staff',
            'is_superuser',
            'date_joined'
        ]
        read_only_fields = ['date_joined', 'username', 'email']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class InstructorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = InstructorProfile
        fields = [
            'user',
            'about',
            'expertise_areas',
            'total_students',
            'total_courses',
            'total_reviews',
            'average_rating',
            'verified',
            'is_featured'
        ]
        read_only_fields = [
            'total_students',
            'total_courses',
            'total_reviews',
            'average_rating',
            'verified',
            'is_featured'
        ]


from .models import InstructorApplication

class InstructorApplicationSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = InstructorApplication
        fields = [
            'id',
            'user',
            'user_details',
            'qualifications',
            'certifications',
            'demo_video',
            'status',
            'admin_note',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['user', 'status', 'admin_note', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label="Confirm New Password")

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Mật khẩu mới không khớp."})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "Mật khẩu mới phải khác mật khẩu hiện tại."})
        return attrs
