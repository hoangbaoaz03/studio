"""
DRF Serializers for User and Instructor API
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, InstructorProfile


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
            'is_instructor',
            'date_joined'
        ]
        read_only_fields = ['date_joined']


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
