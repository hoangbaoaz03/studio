"""
Result/Enrollment models for marketplace
Replaces academic grading system with enrollment tracking
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from course.models import Course, Lecture


class Enrollment(models.Model):
    """
    Student enrollment in a course
    Replaces TakenCourse - focuses on access and progress, not grades
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    # Purchase info
    price_paid = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text=_("Price paid at enrollment")
    )
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=200, blank=True)
    
    # Progress tracking
    progress_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_accessed_lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    
    # Timestamps
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    # B2B Link
    organization = models.ForeignKey(
        'organization.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollments'
    )
    
    class Meta:
        ordering = ['-enrolled_at']
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', '-enrolled_at']),
            models.Index(fields=['course', '-enrolled_at']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def update_progress(self):
        """Calculate completion percentage based on watched lectures"""
        from course.models import Lecture
        # Count actual lectures in the course (not cached value)
        total_lectures = Lecture.objects.filter(section__course=self.course).count()
        if total_lectures == 0:
            self.progress_percent = 0
            self.save()
            return
        
        completed_lectures = LectureProgress.objects.filter(
            enrollment=self,
            completed=True
        ).count()
        
        self.progress_percent = min(
            round((completed_lectures / total_lectures) * 100, 2),
            100.00
        )
        
        # Mark as completed if 100%
        if self.progress_percent >= 100 and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        # Reset completed_at if progress drops below 100%
        elif self.progress_percent < 100 and self.completed_at:
            self.completed_at = None
        
        self.save()


class LectureProgress(models.Model):
    """
    Track individual lecture watch progress
    """
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lecture_progress'
    )
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    
    # Progress
    completed = models.BooleanField(default=False)
    last_position = models.IntegerField(
        default=0,
        help_text=_("Last watched position in seconds")
    )
    watch_count = models.IntegerField(default=0)
    
    # Timestamps
    first_watched = models.DateTimeField(auto_now_add=True)
    last_watched = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # B2B Link & detailed tracking
    organization = models.ForeignKey(
        'organization.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lecture_progresses'
    )
    watched_seconds = models.IntegerField(default=0, help_text=_("Total seconds watched"))
    
    class Meta:
        unique_together = ['enrollment', 'lecture']
        indexes = [
            models.Index(fields=['enrollment', 'completed']),
        ]
    
    def __str__(self):
        status = "Completed" if self.completed else f"{self.last_position}s"
        return f"{self.enrollment.student.username} - {self.lecture.title} ({status})"
    
    def mark_complete(self):
        """Mark lecture as completed"""
        if not self.completed:
            from django.utils import timezone
            self.completed = True
            self.completed_at = timezone.now()
            self.save()
            
            # Update enrollment progress
            self.enrollment.update_progress()
    
    def mark_incomplete(self):
        """Mark lecture as not completed"""
        if self.completed:
            self.completed = False
            self.completed_at = None
            self.save()
            
            # Update enrollment progress
            self.enrollment.update_progress()


class Review(models.Model):
    """
    Course reviews and ratings
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='review'
    )
    
    # Review content
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("1-5 stars")
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    
    # Helpfulness voting
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Status
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Featured review on course page")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['course', '-helpful_count']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update course rating
        self.course.update_stats()


class ReviewHelpful(models.Model):
    """
    Track who marked a review as helpful/not helpful
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpfulness_votes'
    )
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'review']
    
    def __str__(self):
        vote = "👍" if self.is_helpful else "👎"
        return f"{self.user.username} {vote} {self.review}"


class Question(models.Model):
    """
    Q&A for lectures
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    
    # Question
    title = models.CharField(max_length=200)
    question = models.TextField()
    
    # Video timestamp (optional)
    timestamp = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Second in video where question applies")
    )
    
    # Status
    is_answered = models.BooleanField(default=False)
    answer_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['lecture', '-created_at']),
            models.Index(fields=['course', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"


class Answer(models.Model):
    """
    Answers to questions
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    
    answer = models.TextField()
    
    # Metadata
    is_instructor_answer = models.BooleanField(default=False)
    upvote_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_instructor_answer', '-upvote_count', 'created_at']
    
    def __str__(self):
        return f"Answer by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Check if user is one of the course instructors
        if self.question.course.courseinstructors.filter(instructor=self.user).exists():
            self.is_instructor_answer = True
        super().save(*args, **kwargs)
        
        # Update question answer count
        self.question.answer_count = self.question.answers.count()
        if self.question.answer_count > 0:
            self.question.is_answered = True
        self.question.save()


class Wishlist(models.Model):
    """
    User's wishlist for courses
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} → {self.course.title}"


class Note(models.Model):
    """
    User notes taken during video playback
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    content = models.TextField()
    timestamp = models.IntegerField(
        help_text=_("Timestamp in seconds where note was taken")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['lecture', 'timestamp']),
        ]
        
    def __str__(self):
        return f"Note by {self.user.username} at {self.timestamp}s"


class QuizResult(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_results'
    )
    quiz = models.ForeignKey(
        'course.Lecture',
        on_delete=models.CASCADE,
        limit_choices_to={'lecture_type': 'quiz'}
    )
    attempt_number = models.IntegerField(default=1)
    score_achieved = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_passed = models.BooleanField(default=False)
    attempt_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'quiz', 'attempt_number']

class StudentAnswer(models.Model):
    result = models.ForeignKey(
        QuizResult,
        on_delete=models.CASCADE,
        related_name='student_answers'
    )
    question = models.ForeignKey(
        'course.QuizQuestion',
        on_delete=models.CASCADE
    )
    selected_answer = models.ForeignKey(
        'course.QuizAnswer',
        on_delete=models.CASCADE
    )
    is_correct = models.BooleanField(default=False, help_text="Denormalized for performance")

    class Meta:
        indexes = [
            models.Index(fields=['result']),
        ]

