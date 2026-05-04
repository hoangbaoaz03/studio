"""
Course models for marketplace platform
Udemy-like course structure with categories, pricing, and content
"""
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
import uuid


class Category(MPTTModel):
    """
    Top-level course categories
    Examples: Development, Business, Design, Marketing
    """
    name = models.CharField(max_length=100, unique=True)
    name_vi = models.CharField(max_length=100, blank=True, null=True, help_text=_("Vietnamese name"))
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Icon class name (e.g., 'fas fa-code')")
    )
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    
    class MPTTMeta:
        order_insertion_by = ['order', 'name']

    class Meta:
        verbose_name_plural = "Categories"
        # MPTT models usually don't need 'ordering' in Meta as it's handled by MPTT, 
        # but if we want flat ordering we can keep it. MPTTMeta handles tree ordering.
        # ordering = ['order', 'name'] 
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def course_count(self):
        # Count courses in this category and all subcategories
        Course = self.courses.model
        categories = self.get_descendants(include_self=True)
        return Course.objects.filter(category__in=categories, status='published').count()


class Subcategory(models.Model):
    """
    Second-level categories
    Examples: Web Development, Mobile Development, Game Development
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Subcategories"
        ordering = ['order', 'name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} > {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.category.name}-{self.name}")
            self.slug = base_slug
        super().save(*args, **kwargs)
    
    @property
    def course_count(self):
        return self.courses.filter(status='published').count()


class CourseInstructor(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='courseinstructors')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_instructor': True}
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ['course', 'instructor']

    def __str__(self):
        return f"{self.instructor} - {self.course}"


class Course(models.Model):
    """
    Core course model for marketplace
    Instructor creates, students purchase
    """
    LEVEL_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('all', _('All Levels')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending Review')),
        ('published', _('Published')),
        ('paused', _('Paused')),
        ('scheduled', _('Scheduled')),
        ('archived', _('Archived')),
    ]
    
    # Core info
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    instructors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CourseInstructor',
        related_name='instructored_courses'
    )
    
    # Basic details
    title = models.CharField(max_length=200)
    title_vi = models.CharField(max_length=200, blank=True, null=True, help_text=_("Vietnamese title"))
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Short catchy subtitle")
    )
    subtitle_vi = models.CharField(max_length=200, blank=True, null=True, help_text=_("Vietnamese subtitle"))
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses'
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    
    # Description
    description = models.TextField(
        help_text=_("Full course description (supports Markdown)")
    )
    description_vi = models.TextField(blank=True, null=True, help_text=_("Vietnamese description"))
    what_you_will_learn = models.JSONField(
        default=list,
        help_text=_("List of learning outcomes")
    )
    what_you_will_learn_vi = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Vietnamese learning outcomes")
    )
    requirements = models.JSONField(
        default=list,
        help_text=_("Prerequisites and requirements")
    )
    requirements_vi = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Vietnamese requirements")
    )
    target_audience = models.JSONField(
        default=list,
        help_text=_("Who this course is for")
    )
    target_audience_vi = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Vietnamese target audience")
    )
    
    # Media
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/',
        blank=True,
        null=True
    )
    promo_video_url = models.URLField(
        blank=True,
        help_text=_("Promotional video URL (YouTube, Vimeo, or S3)")
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    discount_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Promotional price (optional)")
    )
    is_free = models.BooleanField(default=False)
    
    # Course metadata
    language = models.CharField(
        max_length=50,
        default='English',
        help_text=_("Primary language of instruction")
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='all'
    )
    
    # Stats (denormalized)
    total_duration = models.IntegerField(
        default=0,
        help_text=_("Total course duration in seconds")
    )
    total_lectures = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_featured = models.BooleanField(default=False)
    
    # Engagement
    welcome_message = models.TextField(
        blank=True,
        help_text=_("Message sent to students upon enrollment")
    )
    congratulations_message = models.TextField(
        blank=True,
        help_text=_("Message sent to students upon completion")
    )

    is_active = models.BooleanField(default=True, help_text=_("Admin control to hide course"))
    
    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['-average_rating']),
            models.Index(fields=['-total_enrollments']),
        ]
    
    def __str__(self):
        return self.title

    @property
    def instructor(self):
        primary = self.courseinstructors.filter(is_primary=True).first()
        if primary:
            return primary.instructor
        return self.instructors.first()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @property
    def current_price(self):
        """Get the effective price (discount or regular)"""
        if self.is_free:
            return 0
        return self.discount_price if self.discount_price else self.price
    
    @property
    def has_discount(self):
        return bool(self.discount_price and self.discount_price < self.price)
    
    @property
    def discount_percentage(self):
        if not self.has_discount:
            return 0
        return int(((self.price - self.discount_price) / self.price) * 100)
    
    def update_stats(self):
        """Recalculate course statistics"""
        # Total duration and lectures
        lectures = self.sections.all().prefetch_related('lectures')
        total_duration = 0
        total_lectures_count = 0
        
        for section in lectures:
            section_lectures = section.lectures.all()
            total_lectures_count += section_lectures.count()
            total_duration += sum(
                lecture.duration for lecture in section_lectures
            )
        
        self.total_duration = total_duration
        self.total_lectures = total_lectures_count
        
        # Enrollments
        self.total_enrollments = self.enrollments.count()
        
        # Reviews and rating
        reviews = self.reviews.all()
        self.total_reviews = reviews.count()
        if self.total_reviews > 0:
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.average_rating = round(avg, 2)
        
        self.save()


class Section(models.Model):
    """
    Course curriculum sections
    Groups related lectures together
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    title = models.CharField(max_length=200)
    objective = models.TextField(
        blank=True,
        help_text=_("Learning objective for this section")
    )
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def total_duration(self):
        """Total duration of all lectures in this section"""
        return sum(lecture.duration for lecture in self.lectures.all())
    
    @property
    def lecture_count(self):
        return self.lectures.count()


class Lecture(models.Model):
    """
    Individual learning units within sections
    Supports Video, Content, and Resources
    """
    LECTURE_TYPES = [
        ('video', _('Video')),
        ('article', _('Article')),
        ('file', _('File/Resource')),
        ('quiz', _('Quiz')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('paused', _('Paused')),
        ('scheduled', _('Scheduled')),
        ('processing', _('Processing')),
    ]
    
    VIDEO_SOURCES = [
        ('upload', _('Direct Upload')),
        ('youtube', _('YouTube')),
        ('vimeo', _('Vimeo')),
        ('external', _('External URL')),
    ]

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='lectures'
    )
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    
    # Classification
    lecture_type = models.CharField(
        max_length=20,
        choices=LECTURE_TYPES,
        default='video'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Video Content
    video_source = models.CharField(
        max_length=20,
        choices=VIDEO_SOURCES,
        default='upload',
        blank=True
    )
    video_file = models.FileField(
        upload_to='course_videos/',
        blank=True,
        null=True,
        help_text=_("Direct video file upload")
    )
    video_url = models.URLField(
        blank=True,
        help_text=_("URL for YouTube/Vimeo or public file")
    )
    asset_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("External ID or S3 Key")
    )
    duration = models.IntegerField(
        default=0,
        help_text=_("Duration in seconds")
    )
    duration_minutes = models.IntegerField(
        default=0,
        help_text=_("Estimated completion time in minutes")
    )
    max_attempts = models.IntegerField(
        default=1,
        help_text=_("Max attempts if lecture type is quiz")
    )
    published_at = models.DateTimeField(null=True, blank=True, help_text=_("Scheduled publish time"))
    
    # Text/Article Content
    content = models.TextField(
        blank=True,
        help_text=_("Short description or summary")
    )
    article_content = models.TextField(
        blank=True,
        help_text=_("Main content for Article type (Markdown supported)")
    )
    
    # Resources (Legacy/JSON way - consider using CourseResource for files)
    resources = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Downloadable resources (legacy)")
    )
    
    # Preview
    is_preview = models.BooleanField(
        default=False,
        help_text=_("Free preview lecture")
    )
    admin_note = models.TextField(blank=True, help_text=_("Internal admin notes/rejection reason"))
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
        unique_together = ['section', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot original video fields so post_save signal can detect real changes
        self._original_video_file = self.video_file.name if self.video_file else None
        self._original_video_url = self.video_url or None

    def __str__(self):
        return f"{self.section.course.title} - {self.title} ({self.lecture_type})"


class CourseResource(models.Model):
    """
    Downloadable resources attached to lectures
    """
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='course_resources'
    )
    title = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='course_resources/',
        help_text=_("PDF, ZIP, code files, etc.")
    )
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField(help_text=_("Size in bytes"))
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    

class Announcement(models.Model):
    """
    Course announcements/notifications from instructor
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_announcements'
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
        ]
        
    def __str__(self):
        return f"Announcement: {self.title} ({self.course.title})"


class QuizQuestion(models.Model):
    """
    Questions for a quiz lecture
    """
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='quiz_questions',
        limit_choices_to={'lecture_type': 'quiz'}
    )
    question_text = models.TextField()
    explanation = models.TextField(blank=True, help_text=_("Explanation for the correct answer"))
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
        
    def __str__(self):
        return f"Q: {self.question_text[:50]}"


class QuizAnswer(models.Model):
    """
    Answers for a quiz question
    """
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.answer_text

