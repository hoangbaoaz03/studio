"""
Admin configuration for enrollments and reviews
"""
from django.contrib import admin
from .models import (
    Enrollment,
    LectureProgress,
    Review,
    ReviewHelpful,
    Question,
    Answer,
    Wishlist
)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'course',
        'price_paid',
        'progress_percent',
        'enrolled_at',
        'completed_at',
        'certificate_issued'
    ]
    list_filter = ['certificate_issued', 'enrolled_at', 'completed_at']
    search_fields = ['student__username', 'course__title', 'transaction_id']
    readonly_fields = ['enrolled_at', 'last_accessed']
    
    fieldsets = (
        ('Enrollment Info', {
            'fields': ('student', 'course')
        }),
        ('Purchase', {
            'fields': ('price_paid', 'payment_method', 'transaction_id')
        }),
        ('Progress', {
            'fields': (
                'progress_percent',
                'last_accessed_lecture',
                'last_accessed'
            )
        }),
        ('Completion', {
            'fields': (
                'enrolled_at',
                'completed_at',
                'certificate_issued',
                'certificate_number'
            )
        }),
    )
    
    actions = ['recalculate_progress']
    
    def recalculate_progress(self, request, queryset):
        for enrollment in queryset:
            enrollment.update_progress()
        self.message_user(request, f'Recalculated progress for {queryset.count()} enrollments.')
    recalculate_progress.short_description = "Recalculate progress"


@admin.register(LectureProgress)
class LectureProgressAdmin(admin.ModelAdmin):
    list_display = [
        'enrollment',
        'lecture',
        'completed',
        'last_position',
        'watch_count',
        'last_watched'
    ]
    list_filter = ['completed', 'last_watched']
    search_fields = [
        'enrollment__student__username',
        'lecture__title',
        'lecture__section__course__title'
    ]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'course',
        'rating',
        'title',
        'helpful_count',
        'is_featured',
        'created_at'
    ]
    list_filter = ['rating', 'is_featured', 'created_at']
    search_fields = ['student__username', 'course__title', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['feature_reviews']
    
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} reviews featured.')
    feature_reviews.short_description = "Feature selected reviews"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'lecture',
        'title',
        'is_answered',
        'answer_count',
        'created_at'
    ]
    list_filter = ['is_answered', 'created_at']
    search_fields = ['user__username', 'lecture__title', 'title', 'question']


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['user', 'answer', 'is_instructor_answer', 'upvote_count']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        'question',
        'user',
        'is_instructor_answer',
        'upvote_count',
        'created_at'
    ]
    list_filter = ['is_instructor_answer', 'created_at']
    search_fields = ['user__username', 'question__title', 'answer']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'course__title']
