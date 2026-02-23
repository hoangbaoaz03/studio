from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from analytics.models import DailyMetric
from accounts.models import User
from course.models import Course
from result.models import Enrollment
from payments.models import Transaction
from datetime import timedelta

class Command(BaseCommand):
    help = 'Calculates daily metrics for the previous day (or specified date)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=1, help='Number of days back to calculate')
        parser.add_argument('--date', type=str, help='Specific date YYYY-MM-DD')

    def handle(self, *args, **kwargs):
        if kwargs['date']:
            target_date = timezone.datetime.strptime(kwargs['date'], '%Y-%m-%d').date()
        else:
            target_date = (timezone.now() - timedelta(days=kwargs['days'])).date()
            
        self.stdout.write(f"Calculating metrics for {target_date}...")
        
        # Define ranges
        start_of_day = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time()))
        end_of_day = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.max.time()))
        
        # 1. User Metrics
        new_users = User.objects.filter(date_joined__range=(start_of_day, end_of_day)).count()
        total_users = User.objects.filter(date_joined__lte=end_of_day).count()
        active_users = User.objects.filter(last_login__range=(start_of_day, end_of_day)).count()
        
        # 2. Financial Metrics
        daily_transactions = Transaction.objects.filter(
            created_at__range=(start_of_day, end_of_day),
            status='completed'
        )
        total_revenue = daily_transactions.aggregate(Sum('gross_amount'))['gross_amount__sum'] or 0
        platform_revenue = daily_transactions.aggregate(Sum('platform_fee'))['platform_fee__sum'] or 0
        
        # 3. Content Metrics
        new_courses = Course.objects.filter(created_at__range=(start_of_day, end_of_day)).count()
        new_enrollments = Enrollment.objects.filter(created_at__range=(start_of_day, end_of_day)).count()
        
        # Save DailyMetric
        metric, created = DailyMetric.objects.update_or_create(
            date=target_date,
            defaults={
                'new_users': new_users,
                'active_users': active_users,
                'total_users': total_users,
                'total_revenue': total_revenue,
                'platform_revenue': platform_revenue,
                'new_courses': new_courses,
                'total_enrollments': new_enrollments,
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f"Successfully calculated metrics for {target_date}"))
