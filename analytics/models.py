from django.db import models
from course.models import Course

class DailyMetric(models.Model):
    """
    Daily snapshot of platform performance.
    Calculated via cron job every midnight.
    """
    date = models.DateField(unique=True, db_index=True)
    
    # User Growth
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0) # Logged in today
    total_users = models.PositiveIntegerField(default=0) # Cumulative
    
    # Financials
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    platform_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Engagement
    new_courses = models.PositiveIntegerField(default=0)
    total_enrollments = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'

    def __str__(self):
        return f"Metrics for {self.date}"

class CourseMetric(models.Model):
    """
    Daily performance per course (for top lists/trending)
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='daily_metrics')
    date = models.DateField(db_index=True)
    
    views = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_enrollments = models.PositiveIntegerField(default=0)
    rating_avg = models.FloatField(default=0)
    
    class Meta:
        unique_together = ['course', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.course.title} on {self.date}"
