"""
DRF Serializers for Course API
"""
from rest_framework import serializers
from .models import Category, Subcategory, Course, Section, Lecture


class CategorySerializer(serializers.ModelSerializer):
    course_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'description', 'order', 'is_active', 'course_count']


class SubcategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    course_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Subcategory
        fields = ['id', 'category', 'category_name', 'name', 'slug', 'description', 'order', 'is_active', 'course_count']


class LectureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture
        fields = [
            'id',
            'title',
            'order',
            'video_url',
            'duration',
            'content',
            'is_preview',
            'created_at'
        ]
        read_only_fields = ['created_at']


class SectionSerializer(serializers.ModelSerializer):
    lectures = LectureSerializer(many=True, read_only=True)
    total_duration = serializers.ReadOnlyField()
    lecture_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Section
        fields = [
            'id',
            'title',
            'objective',
            'order',
            'lectures',
            'total_duration',
            'lecture_count'
        ]


class CourseListSerializer(serializers.ModelSerializer):
    """
    Minimal course data for list views
    """
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    current_price = serializers.ReadOnlyField()
    has_discount = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = [
            'id',
            'uuid',
            'slug',
            'title',
            'subtitle',
            'instructor_name',
            'category_name',
            'thumbnail',
            'price',
            'discount_price',
            'current_price',
            'has_discount',
            'discount_percentage',
            'is_free',
            'level',
            'language',
            'total_lectures',
            'total_duration',
            'total_enrollments',
            'average_rating',
            'total_reviews',
            'created_at'
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Full course details including curriculum
    """
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    instructor_id = serializers.IntegerField(source='instructor.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    sections = SectionSerializer(many=True, read_only=True)
    current_price = serializers.ReadOnlyField()
    has_discount = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = [
            'id',
            'uuid',
            'slug',
            'title',
            'subtitle',
            'instructor_id',
            'instructor_name',
            'category',
            'category_name',
            'subcategory',
            'subcategory_name',
            'description',
            'what_you_will_learn',
            'requirements',
            'target_audience',
            'thumbnail',
            'promo_video_url',
            'price',
            'discount_price',
            'current_price',
            'has_discount',
            'discount_percentage',
            'is_free',
            'language',
            'level',
            'total_duration',
            'total_lectures',
            'total_enrollments',
            'total_reviews',
            'average_rating',
            'status',
            'is_featured',
            'sections',
            'created_at',
            'updated_at',
            'published_at'
        ]


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for instructors to create/update courses
    """
    class Meta:
        model = Course
        fields = [
            'title',
            'subtitle',
            'category',
            'subcategory',
            'description',
            'what_you_will_learn',
            'requirements',
            'target_audience',
            'thumbnail',
            'promo_video_url',
            'price',
            'discount_price',
            'is_free',
            'language',
            'level',
        ]
    
    def create(self, validated_data):
        # Set instructor from request user
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)
