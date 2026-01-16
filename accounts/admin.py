"""
Admin configuration for marketplace accounts
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, InstructorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_instructor',
        'email_verified',
        'date_joined'
    ]
    list_filter = ['is_instructor', 'is_staff', 'is_superuser', 'email_verified', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'profile_photo', 'bio', 'headline')}),
        ('Social Links', {'fields': ('website', 'linkedin', 'twitter', 'youtube')}),
        ('Permissions', {
            'fields': ('is_instructor', 'email_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_instructor'),
        }),
    )
    
    actions = ['make_instructor', 'verify_email']
    
    def make_instructor(self, request, queryset):
        updated = queryset.update(is_instructor=True)
        self.message_user(request, f'{updated} users upgraded to instructor.')
    make_instructor.short_description = "Make selected users instructors"
    
    def verify_email(self, request, queryset):
        updated = queryset.update(email_verified=True)
        self.message_user(request, f'{updated} emails verified.')
    verify_email.short_description = "Verify selected user emails"


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'total_students',
        'total_courses',
        'average_rating',
        'total_revenue',
        'verified',
        'is_featured'
    ]
    list_filter = ['verified', 'is_featured', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'total_students',
        'total_courses',
        'total_reviews',
        'average_rating',
        'total_revenue',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Instructor', {
            'fields': ('user',)
        }),
        ('About', {
            'fields': ('about', 'expertise_areas')
        }),
        ('Statistics', {
            'fields': (
                'total_students',
                'total_courses',
                'total_reviews',
                'average_rating',
                'total_revenue'
            )
        }),
        ('Status', {
            'fields': ('verified', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['update_stats', 'feature_instructors']
    
    def update_stats(self, request, queryset):
        for profile in queryset:
            profile.update_stats()
        self.message_user(request, f'Updated stats for {queryset.count()} instructors.')
    update_stats.short_description = "Update instructor statistics"
    
    def feature_instructors(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} instructors featured.')
    feature_instructors.short_description = "Feature selected instructors"
