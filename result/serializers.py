"""
DRF Serializers for Enrollment and Reviews
"""
from rest_framework import serializers
from .models import Enrollment, LectureProgress, Review, Question, Answer, Wishlist


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'course',
            'course_title',
            'course_slug',
            'course_thumbnail',
            'price_paid',
            'progress_percent',
            'enrolled_at',
            'last_accessed',
            'completed_at',
            'certificate_issued'
        ]
        read_only_fields = [
            'progress_percent',
            'enrolled_at',
            'last_accessed',
            'completed_at',
            'certificate_issued'
        ]


class LectureProgressSerializer(serializers.ModelSerializer):
    lecture_title = serializers.CharField(source='lecture.title', read_only=True)
    
    class Meta:
        model = LectureProgress
        fields = [
            'id',
            'lecture',
            'lecture_title',
            'completed',
            'last_position',
            'watch_count',
            'last_watched'
        ]
        read_only_fields = ['watch_count', 'last_watched']


class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_photo = serializers.ImageField(source='student.profile_photo', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id',
            'student',
            'student_name',
            'student_photo',
            'course',
            'rating',
            'title',
            'comment',
            'helpful_count',
            'not_helpful_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['student', 'helpful_count', 'not_helpful_count', 'created_at', 'updated_at']


class AnswerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Answer
        fields = [
            'id',
            'question',
            'user',
            'user_name',
            'answer',
            'is_instructor_answer',
            'upvote_count',
            'created_at'
        ]
        read_only_fields = ['user', 'is_instructor_answer', 'upvote_count', 'created_at']


class QuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id',
            'user',
            'user_name',
            'lecture',
            'title',
            'question',
            'timestamp',
            'is_answered',
            'answer_count',
            'created_at',
            'answers'
        ]
        read_only_fields = ['user', 'is_answered', 'answer_count', 'created_at']


class WishlistSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_slug = serializers.CharField(source='course.slug', read_only=True)
    course_price = serializers.DecimalField(source='course.current_price', max_digits=8, decimal_places=2, read_only=True)
    course_thumbnail = serializers.ImageField(source='course.thumbnail', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = [
            'id',
            'course',
            'course_title',
            'course_slug',
            'course_price',
            'course_thumbnail',
            'added_at'
        ]
        read_only_fields = ['added_at']
