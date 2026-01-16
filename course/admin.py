"""
Admin configuration for marketplace courses
"""
from django.contrib import admin
from .models import Category, Subcategory, Course, Section, Lecture, CourseResource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active', 'course_count']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'order', 'is_active', 'course_count']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category__name']
    prepopulated_fields = {'slug': ('name',)}


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1
    fields = ['title', 'order', 'objective']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'instructor',
        'category',
        'price',
        'status',
        'total_enrollments',
        'average_rating',
        'created_at'
    ]
    list_filter = ['status', 'category', 'level', 'is_featured', 'created_at']
    search_fields = ['title', 'instructor__username', 'instructor__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'uuid',
        'total_duration',
        'total_lectures',
        'total_enrollments',
        'total_reviews',
        'average_rating',
        'created_at',
        'updated_at'
    ]
    inlines = [SectionInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('instructor', 'title', 'subtitle', 'slug', 'uuid')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory')
        }),
        ('Description', {
            'fields': ('description', 'what_you_will_learn', 'requirements', 'target_audience')
        }),
        ('Media', {
            'fields': ('thumbnail', 'promo_video_url')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'is_free')
        }),
        ('Metadata', {
            'fields': ('language', 'level')
        }),
        ('Statistics', {
            'fields': (
                'total_duration',
                'total_lectures',
                'total_enrollments',
                'total_reviews',
                'average_rating'
            )
        }),
        ('Status', {
            'fields': ('status', 'is_featured', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['publish_courses', 'feature_courses']
    
    def publish_courses(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} courses published.')
    publish_courses.short_description = "Publish selected courses"
    
    def feature_courses(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} courses featured.')
    feature_courses.short_description = "Feature selected courses"


class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 1
    fields = ['title', 'order', 'video_url', 'duration', 'is_preview']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'lecture_count']
    list_filter = ['course']
    search_fields = ['title', 'course__title']
    inlines = [LectureInline]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ['title', 'section', 'order', 'duration', 'is_preview']
    list_filter = ['section__course', 'is_preview']
    search_fields = ['title', 'section__title', 'section__course__title']


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'lecture', 'file_type', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'lecture__title']
