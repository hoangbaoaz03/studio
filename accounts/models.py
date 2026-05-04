"""
User models for marketplace platform
Simplified from academic LMS to online course marketplace
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model for marketplace
    Removed: is_student, is_parent, is_dep_head (academic roles)
    Added: is_instructor, email_verified
    """
    # Role
    is_instructor = models.BooleanField(
        default=False,
        help_text=_("Can create and sell courses")
    )
    is_business = models.BooleanField(
        default=False,
        help_text=_("Business/Enterprise user")
    )
    
    # Profile
    email_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    bio = models.TextField(
        blank=True,
        max_length=500,
        help_text=_("Short bio for profile")
    )
    headline = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Professional headline (e.g., 'Web Developer at Google')")
    )
    
    # Social links
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    youtube = models.URLField(blank=True)
    
    deleted_at = models.DateTimeField(null=True, blank=True, help_text=_("Soft delete timestamp"))
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


class InstructorProfile(models.Model):
    """
    Extended profile for instructors
    Marketplace-specific instructor data and analytics
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_profile'
    )
    
    # About
    about = models.TextField(
        blank=True,
        help_text=_("Detailed bio for instructor page")
    )
    
    # Teaching
    expertise_areas = models.JSONField(
        default=list,
        help_text=_("List of expertise areas")
    )
    
    # Stats (denormalized for performance)
    total_students = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    
    # Revenue (for instructor dashboard)
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    # Status
    is_featured = models.BooleanField(
        default=False,
        help_text=_("Featured instructor on homepage")
    )
    verified = models.BooleanField(
        default=False,
        help_text=_("Verified instructor badge")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_students']
    
    def __str__(self):
        return f"Instructor: {self.user.get_full_name() or self.user.username}"
    
    def update_stats(self):
        """Recalculate instructor statistics"""
        from django.apps import apps
        
        Course = apps.get_model('course', 'Course')
        Enrollment = apps.get_model('result', 'Enrollment')
        Review = apps.get_model('result', 'Review')
        
        # Total courses
        self.total_courses = Course.objects.filter(
            instructor=self.user,
            status='published'
        ).count()
        
        # Total students (unique enrollments)
        self.total_students = Enrollment.objects.filter(
            course__instructor=self.user
        ).values('student').distinct().count()
        
        # Reviews and rating
        reviews = Review.objects.filter(course__instructor=self.user)
        self.total_reviews = reviews.count()
        if self.total_reviews > 0:
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.average_rating = round(avg, 2)
        
        self.save()


class InstructorApplication(models.Model):
    """
    Model for managing instructor applications/upgrades
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('needs_update', _('Needs Update')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_applications'
    )
    qualifications = models.TextField(
        help_text=_("Professional qualifications, degrees, and teaching experience")
    )
    certifications = models.FileField(
        upload_to='instructor_applications/certs/',
        blank=True,
        null=True,
        help_text=_("PDF or Image of relevant certifications")
    )
    demo_video = models.FileField(
        upload_to='instructor_applications/demos/',
        blank=True,
        null=True,
        help_text=_("Short demo teaching video")
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    admin_note = models.TextField(
        blank=True,
        help_text=_("Reason for rejection or request for more information")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Application by {self.user.username} - {self.get_status_display()}"
