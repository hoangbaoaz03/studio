"""
Admin configuration for core app
"""
from django.contrib import admin
from .models import SiteSettings, Announcement, ActivityLog


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'default_platform_fee_percent', 'maintenance_mode')
    fieldsets = (
        ('Basic Info', {
            'fields': ('site_name', 'tagline', 'site_description')
        }),
        ('Contact', {
            'fields': ('contact_email', 'support_email')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'youtube_url')
        }),
        ('Platform Settings', {
            'fields': ('default_platform_fee_percent',)
        }),
        ('Features', {
            'fields': ('enable_course_reviews', 'enable_qa', 'enable_wishlist', 'enable_certificates')
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'is_active', 'show_on_homepage', 'start_date', 'end_date')
    list_filter = ('announcement_type', 'is_active', 'show_on_homepage')
    search_fields = ('title', 'message')
    date_hierarchy = 'start_date'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'message', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('message',)
    readonly_fields = ('action', 'user', 'message', 'metadata', 'created_at')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
