from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from .models import DailyMetric
from .serializers import DashboardAnalyticsSerializer
from course.models import Course, Category
from payments.models import Transaction

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get aggregated dashboard analytics.
        Query params:
        - period: '7d', '30d', '90d', 'all' (default: 30d)
        """
        period = request.query_params.get('period', '30d')
        days = 30
        if period == '7d':
            days = 7
        elif period == '90d':
            days = 90
        elif period == 'all':
            days = 365 # Cap at 1 year for now to avoid overload
            
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 1. Fetch Daily Metrics (Trend & Summary)
        daily_metrics = DailyMetric.objects.filter(date__range=(start_date, end_date)).order_by('date')
        
        # Calculate Summary
        total_revenue = daily_metrics.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0
        platform_revenue = daily_metrics.aggregate(Sum('platform_revenue'))['platform_revenue__sum'] or 0
        new_users_period = daily_metrics.aggregate(Sum('new_users'))['new_users__sum'] or 0
        
        # Get latest total_users count (or from last metric)
        last_metric = daily_metrics.last()
        total_users = last_metric.total_users if last_metric else 0
        
        # Active courses (Snapshot)
        active_courses = Course.objects.filter(status='published').count()
        
        summary_data = {
            'total_revenue': total_revenue,
            'platform_revenue': platform_revenue,
            'total_users': total_users, # Current total
            'active_courses': active_courses
        }
        
        # Format Trend Data
        trend_data = []
        for m in daily_metrics:
            trend_data.append({
                'date': m.date,
                'revenue': m.total_revenue,
                'new_users': m.new_users
            })
            
        # 2. Top Courses (from Transactions in period)
        # We query Transaction directly for accurate "in-period" best sellers
        top_courses_qs = Transaction.objects.filter(
            created_at__date__range=(start_date, end_date),
            status='completed'
        ).values(
            'course__id', 'course__title'
        ).annotate(
            revenue=Sum('gross_amount'),
            enrollments=Count('id')
        ).order_by('-revenue')[:5]
        
        top_courses_data = [
            {
                'id': item['course__id'],
                'title': item['course__title'],
                'revenue': item['revenue'],
                'enrollments': item['enrollments']
            }
            for item in top_courses_qs
        ]
        
        # 3. Category Distribution (by Revenue in period)
        category_qs = Transaction.objects.filter(
            created_at__date__range=(start_date, end_date),
            status='completed',
            course__category__isnull=False
        ).values(
            'course__category__name'
        ).annotate(
            value=Sum('gross_amount') # Or Count('id') for enrollments
        ).order_by('-value')[:5]
        
        category_data = [
            {
                'name': item['course__category__name'],
                'value': item['value']
            }
            for item in category_qs
        ]
        
        response_data = {
            'summary': summary_data,
            'trend': trend_data,
            'top_courses': top_courses_data,
            'category_distribution': category_data
        }
        
        serializer = DashboardAnalyticsSerializer(response_data)
        return Response(serializer.data)
