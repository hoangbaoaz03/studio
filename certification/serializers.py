from rest_framework import serializers
from .models import CertificationProvider, Certification, ExamModule, PracticeExam, Question, UserCertificationProgress

class CertificationProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationProvider
        fields = ['id', 'name', 'slug', 'logo', 'description']

class ExamModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamModule
        fields = ['id', 'title', 'order', 'content', 'video_url', 'duration_minutes']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'explanation', 'points', 'domain', 'answers']

class PracticeExamSerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(source='total_questions', read_only=True)
    
    class Meta:
        model = PracticeExam
        fields = ['id', 'title', 'duration_minutes', 'passing_score', 'questions_count', 'is_randomized']

class CertificationSerializer(serializers.ModelSerializer):
    provider = CertificationProviderSerializer(read_only=True)
    modules_count = serializers.SerializerMethodField()
    exams_count = serializers.SerializerMethodField()

    class Meta:
        model = Certification
        fields = [
            'id', 'title', 'slug', 'provider', 'level', 'description', 
            'price', 'estimated_prep_time', 'pass_rate', 'syllabus',
            'modules_count', 'exams_count', 'created_at', 'badge_image_url'
        ]

    def get_modules_count(self, obj):
        return obj.modules.count()

    def get_exams_count(self, obj):
        return obj.practice_exams.count()

class CertificationDetailSerializer(CertificationSerializer):
    modules = ExamModuleSerializer(many=True, read_only=True)
    practice_exams = PracticeExamSerializer(many=True, read_only=True)

    class Meta(CertificationSerializer.Meta):
        fields = CertificationSerializer.Meta.fields + ['modules', 'practice_exams']
