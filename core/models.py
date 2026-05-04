"""
Core models for marketplace
Simplified from academic system
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """
    Global platform settings
    """
    site_name = models.CharField(max_length=100, default="Studigo")
    tagline = models.CharField(max_length=200, blank=True)
    site_description = models.TextField(blank=True)
    
    # Contact
    contact_email = models.EmailField()
    support_email = models.EmailField()
    
    # Social
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # Platform fees
    default_platform_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        help_text=_("Default commission percentage")
    )
    
    # Features
    enable_course_reviews = models.BooleanField(default=True)
    enable_qa = models.BooleanField(default=True)
    enable_wishlist = models.BooleanField(default=True)
    enable_certificates = models.BooleanField(default=True)
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return self.site_name


class Announcement(models.Model):
    """
    Platform-wide announcements
    Replaces NewsAndEvents
    """
    ANNOUNCEMENT_TYPE_CHOICES = [
        ('info', _('Information')),
        ('promotion', _('Promotion')),
        ('update', _('Platform Update')),
        ('maintenance', _('Maintenance')),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(
        max_length=20,
        choices=ANNOUNCEMENT_TYPE_CHOICES,
        default='info'
    )
    
    # Display
    is_active = models.BooleanField(default=True)
    show_on_homepage = models.BooleanField(default=False)
    
    # Scheduling
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    def is_current(self):
        """Check if announcement is currently active"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        return True


class ActivityLog(models.Model):
    """
    System activity logging
    """
    ACTION_CHOICES = [
        ('course_created', 'Course Created'),
        ('course_published', 'Course Published'),
        ('enrollment', 'Student Enrolled'),
        ('review_posted', 'Review Posted'),
        ('payout_processed', 'Payout Processed'),
        ('user_registered', 'User Registered'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    message = models.TextField()
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional data as JSON")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.created_at}] {self.action}: {self.message}"


class SystemKey(models.Model):
    """
    Dynamic system configuration (Key-Value Store)
    """
    TYPE_CHOICES = [
        ('bool', 'Boolean'),
        ('int', 'Integer'),
        ('float', 'Float'),
        ('string', 'String'),
        ('json', 'JSON'),
    ]

    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(help_text="Raw value (will be cast based on type)")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='string')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False, help_text="Expose to public API?")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['key']
        
    def __str__(self):
        return f"{self.key} ({self.type})"
        
    @property
    def cast_value(self):
        import json
        if self.type == 'bool':
            return self.value.lower() == 'true'
        elif self.type == 'int':
            return int(self.value)
        elif self.type == 'float':
            return float(self.value)
        elif self.type == 'json':
            try:
                return json.loads(self.value)
            except:
                return {}
        return self.value


class Notification(models.Model):
    """
    User notifications for system events
    """
    TYPE_CHOICES = [
        ('system', _('System')),
        ('course', _('Course Announcement')),
        ('learning', _('Bình luận/Hỏi đáp')), # Comment/Q&A
        ('review', _('New Review')),
        ('enrollment', _('New Enrollment')),
    ]
    
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system'
    )
    link = models.CharField(
        max_length=255, 
        blank=True,
        help_text=_("Link to relevant resource (e.g. /course/slug)")
    )
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username}: {self.title}"
