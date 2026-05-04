"""
DRF Serializers for Course API
"""
from rest_framework import serializers
from .models import Category, Subcategory, Course, Section, Lecture, Announcement, QuizQuestion, QuizAnswer


class RecursiveField(serializers.Serializer):
    """
    Serializer field for recursive children
    """
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

class CategorySerializer(serializers.ModelSerializer):
    course_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_vi', 'slug', 'icon', 'description', 'order', 'is_active', 'course_count', 'parent']


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for the full category tree (Mega Menu)
    """
    children = RecursiveField(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'children']


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
            'section',
            'title',
            'order',
            'lecture_type',
            'status',
            'video_source',
            'video_file',
            'video_url',
            'asset_id',
            'duration',
            'content',
            'article_content',
            'is_preview',
            'published_at',
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
            'course',
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
    category_path = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    current_price = serializers.ReadOnlyField()
    has_discount = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    def get_thumbnail(self, obj):
        if not obj.thumbnail:
            return None
        url = str(obj.thumbnail)
        if url.startswith('http') or url.startswith('https'):
            return url
        return obj.thumbnail.url

    def get_category_path(self, obj):
        if obj.category:
            return [cat.name for cat in obj.category.get_ancestors(include_self=True)]
        return []
    
    class Meta:
        model = Course
        fields = [
            'id',
            'uuid',
            'slug',
            'title',
            'title_vi',
            'subtitle',
            'subtitle_vi',
            'instructor_name',
            'category_name',
            'category_path',
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
            'created_at',
            'status',
            'is_active'
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
    thumbnail = serializers.SerializerMethodField()
    current_price = serializers.ReadOnlyField()

    def get_thumbnail(self, obj):
        if not obj.thumbnail:
            return None
        url = str(obj.thumbnail)
        if url.startswith('http') or url.startswith('https'):
            return url
        return obj.thumbnail.url
    has_discount = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Course
        fields = [
            'id',
            'uuid',
            'slug',
            'title',
            'title_vi',
            'subtitle',
            'subtitle_vi',
            'instructor_id',
            'instructor_name',
            'category',
            'category_name',
            'subcategory',
            'subcategory_name',
            'description',
            'description_vi',
            'what_you_will_learn',
            'what_you_will_learn_vi',
            'requirements',
            'requirements_vi',
            'target_audience',
            'target_audience_vi',
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
            'published_at',
            'is_enrolled'
        ]

    is_enrolled = serializers.SerializerMethodField()

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from django.apps import apps
            Enrollment = apps.get_model('result', 'Enrollment')
            return Enrollment.objects.filter(student=request.user, course=obj).exists()
        return False


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for instructors to create/update courses
    """
    # Return these fields in response after creation
    slug = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id',
            'slug',
            'title',
            'subtitle',
            'category',
            'subcategory',
            'description',
            'what_you_will_learn',
            'requirements',
            'target_audience',
            'promo_video_url',
            'price',
            'discount_price',
            'is_free',
            'language',
            'level',
            'status',
            'thumbnail',
            'welcome_message',
            'congratulations_message',
            'published_at',
        ]
        read_only_fields = ['id', 'slug']
    

    def create(self, validated_data):
        # instructor is set via CourseInstructor M2M in perform_create
        return super().create(validated_data)


class AnnouncementSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='user.get_full_name', read_only=True)
    instructor_avatar = serializers.SerializerMethodField()
    created_at_formatted = serializers.DateTimeField(source='created_at', format="%b %d, %Y", read_only=True)
    course_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Announcement
        fields = ['id', 'course_id', 'title', 'content', 'created_at', 'created_at_formatted', 'instructor_name', 'instructor_avatar']
        read_only_fields = ['id', 'created_at', 'instructor_name']

    def get_instructor_avatar(self, obj):
        # Placeholder or actual logic if Profile exists
        return None


class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id', 'answer_text', 'is_correct']


class QuizQuestionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True)
    
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'explanation', 'order', 'answers']
        
    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = QuizQuestion.objects.create(**validated_data)
        for answer_data in answers_data:
            QuizAnswer.objects.create(question=question, **answer_data)
        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', [])
        instance.question_text = validated_data.get('question_text', instance.question_text)
        instance.explanation = validated_data.get('explanation', instance.explanation)
        instance.order = validated_data.get('order', instance.order)
        instance.save()
        
        # Naive update: delete old answers and create new ones (simplifies logic)
        instance.answers.all().delete()
        for answer_data in answers_data:
            QuizAnswer.objects.create(question=instance, **answer_data)
            
        return instance
