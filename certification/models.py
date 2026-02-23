from django.db import models
from django.conf import settings
from django.utils.text import slugify

class CertificationProvider(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='providers/logos/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Certification(models.Model):
    LEVEL_CHOICES = (
        ('Beginner', 'Beginner'),
        ('Associate', 'Associate'),
        ('Professional', 'Professional'),
        ('Expert', 'Expert'),
    )

    provider = models.ForeignKey(CertificationProvider, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Associate')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Metadata for display
    badge_image_url = models.URLField(blank=True, null=True, help_text="URL to the official certification badge")
    estimated_prep_time = models.CharField(max_length=50, help_text="e.g. '3 months'")
    pass_rate = models.CharField(max_length=10, blank=True, help_text="e.g. '92%'")
    
    # JSON syllabus for simplicity
    syllabus = models.JSONField(default=list, blank=True, help_text="List of topics")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ExamModule(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    content = models.TextField(help_text="Markdown content for the module")
    video_url = models.URLField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.certification.title} - {self.title}"

class PracticeExam(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='practice_exams')
    title = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(default=90)
    passing_score = models.IntegerField(default=70, help_text="Percentage required to pass")
    total_questions = models.IntegerField(default=60)
    is_randomized = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.certification.title} - {self.title}"

class Question(models.Model):
    QUESTION_TYPES = (
        ('MCQ', 'Multiple Choice'),
        ('MSQ', 'Multiple Select'),
    )
    
    exam = models.ForeignKey(PracticeExam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='MCQ')
    explanation = models.TextField(blank=True, help_text="Markdown supported explanation")
    points = models.IntegerField(default=1)
    domain = models.CharField(max_length=100, blank=True, help_text="Exam domain for score breakdown")
    
    # Answers stored as JSON for simplicity in this iteration
    # Structure: [{"id": 1, "text": "Answer A", "is_correct": true}, ...]
    answers = models.JSONField(default=list)

    def __str__(self):
        return self.text[:50]

class UserCertificationProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certification_progress')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    completed_modules = models.ManyToManyField(ExamModule, blank=True)
    completed_exams = models.ManyToManyField(PracticeExam, blank=True)
    
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'certification')
