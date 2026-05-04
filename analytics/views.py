import datetime
import csv
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from .models import DailyMetric
from .serializers import DashboardAnalyticsSerializer
from course.models import Course
from payments.models import Transaction, B2BPayment
from chat.models import ChatMessage


def _get_date_range(period):
    """Return (start_date, end_date) based on period string."""
    days_map = {'7d': 7, '30d': 30, '90d': 90, 'all': 365}
    days = days_map.get(period, 30)
    end_date = timezone.now().date()
    start_date = end_date - datetime.timedelta(days=days)
    return start_date, end_date


def _aggregate_transactions(start_date, end_date):
    """Aggregate transaction data in Python to avoid SQLite timezone issues."""
    start_dt = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_dt = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))
    qs = Transaction.objects.filter(
        status='completed',
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    ).values('created_at', 'gross_amount', 'platform_fee', 'instructor_revenue')

    total_b2c = Decimal('0.00')
    total_platform_fee = Decimal('0.00')
    total_commission = Decimal('0.00')
    tx_by_date = {}  # date -> {'rev': Decimal, 'plat': Decimal}

    for tx in qs:
        amt = tx['gross_amount'] or Decimal('0.00')
        fee = tx['platform_fee'] or Decimal('0.00')
        comm = tx['instructor_revenue'] or Decimal('0.00')
        total_b2c += amt
        total_platform_fee += fee
        total_commission += comm
        d = tx['created_at'].date()
        if d not in tx_by_date:
            tx_by_date[d] = {'rev': Decimal('0.00'), 'plat': Decimal('0.00')}
        tx_by_date[d]['rev'] += amt
        tx_by_date[d]['plat'] += fee

    return total_b2c, total_platform_fee, total_commission, tx_by_date


def _aggregate_b2b(start_date, end_date):
    start_dt = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_dt = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))
    qs = B2BPayment.objects.filter(
        status='approved',
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    ).values('created_at', 'amount')

    total = Decimal('0.00')
    by_date = {}
    for p in qs:
        amt = p['amount'] or Decimal('0.00')
        total += amt
        d = p['created_at'].date()
        by_date[d] = by_date.get(d, Decimal('0.00')) + amt

    return total, by_date


def _aggregate_tokens(start_date, end_date):
    start_dt = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_dt = timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max))
    qs = ChatMessage.objects.filter(
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    ).values('created_at', 'tokens_used')

    total = 0
    by_date = {}
    for msg in qs:
        t = msg['tokens_used'] or 0
        total += t
        d = msg['created_at'].date()
        by_date[d] = by_date.get(d, 0) + t

    return total, by_date


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get aggregated dashboard analytics.
        Query params:
        - period: '7d', '30d', '90d', 'all' (default: 30d)
        """
        try:
            period = request.query_params.get('period', '30d')
            start_date, end_date = _get_date_range(period)

            # Aggregate all revenue data in Python (avoids SQLite timezone issues)
            b2c_revenue, b2c_platform_fee, instructor_commission, tx_by_date = _aggregate_transactions(start_date, end_date)
            b2b_revenue, b2b_by_date = _aggregate_b2b(start_date, end_date)
            ai_tokens_used, tokens_by_date = _aggregate_tokens(start_date, end_date)

            gross_revenue = b2c_revenue + b2b_revenue
            net_revenue = b2c_platform_fee + b2b_revenue  # B2B is 100% platform revenue

            # User metrics from DailyMetric snapshots
            daily_metrics = DailyMetric.objects.filter(
                date__range=(start_date, end_date)
            ).order_by('date')

            last_metric = daily_metrics.last()
            total_users = last_metric.total_users if last_metric else 0
            active_courses = Course.objects.filter(status='published').count()

            summary_data = {
                'gross_revenue': float(gross_revenue),
                'net_revenue': float(net_revenue),
                'b2c_revenue': float(b2c_revenue),
                'b2b_revenue': float(b2b_revenue),
                'instructor_commission': float(instructor_commission),
                'ai_tokens_used': int(ai_tokens_used),
                'total_users': int(total_users),
                'active_courses': int(active_courses),
            }

            # Build trend data per day
            trend_data = []
            for m in daily_metrics:
                day_tx = tx_by_date.get(m.date, {'rev': Decimal('0.00'), 'plat': Decimal('0.00')})
                day_b2c = float(day_tx['rev'])
                day_b2b = float(b2b_by_date.get(m.date, Decimal('0.00')))
                trend_data.append({
                    'date': m.date,
                    'revenue': day_b2c + day_b2b,
                    'b2c_revenue': day_b2c,
                    'b2b_revenue': day_b2b,
                    'ai_tokens_used': tokens_by_date.get(m.date, 0),
                    'new_users': m.new_users,
                })

            # Top 5 courses by revenue (use Python-aggregated tx_by_date logic doesn't work here
            # so we use a safe ORM query with __gte/__lte instead of __date)
            top_courses_qs = Transaction.objects.filter(
                status='completed',
                created_at__gte=timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min)),
                created_at__lte=timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max)),
            ).values('course__id', 'course__title').annotate(
                revenue=Sum('gross_amount'),
                enrollments=Count('id')
            ).order_by('-revenue')[:5]

            top_courses_data = [
                {
                    'id': item['course__id'],
                    'title': item['course__title'],
                    'revenue': float(item['revenue'] or 0),
                    'enrollments': item['enrollments'],
                }
                for item in top_courses_qs
            ]

            # Category distribution
            cat_qs = Transaction.objects.filter(
                status='completed',
                course__category__isnull=False,
                created_at__gte=timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min)),
                created_at__lte=timezone.make_aware(datetime.datetime.combine(end_date, datetime.time.max)),
            ).values('course__category__name').annotate(
                value=Sum('gross_amount')
            ).order_by('-value')[:5]

            category_data = [
                {
                    'name': item['course__category__name'],
                    'value': float(item['value'] or 0),
                }
                for item in cat_qs
            ]

            response_data = {
                'summary': summary_data,
                'trend': trend_data,
                'top_courses': top_courses_data,
                'category_distribution': category_data,
            }

            serializer = DashboardAnalyticsSerializer(response_data)
            return Response(serializer.data)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def export_report(self, request):
        """
        Export financial analytics to CSV for accounting.
        Query params:
        - period: '7d', '30d', '90d', 'all' (default: 30d)
        """
        period = request.query_params.get('period', '30d')
        start_date, end_date = _get_date_range(period)

        daily_metrics = DailyMetric.objects.filter(
            date__range=(start_date, end_date)
        ).order_by('date')

        _, _, _, tx_by_date = _aggregate_transactions(start_date, end_date)
        _, b2b_by_date = _aggregate_b2b(start_date, end_date)
        _, tokens_by_date = _aggregate_tokens(start_date, end_date)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="financial_report_{start_date}_to_{end_date}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Gross Revenue', 'Net Revenue',
            'B2C Revenue', 'B2B Revenue', 'Instructor Commission', 'AI Tokens Used'
        ])

        for m in daily_metrics:
            tx_data = tx_by_date.get(m.date, {'rev': Decimal('0.00'), 'plat': Decimal('0.00')})
            day_b2c = tx_data['rev']
            day_plat = tx_data['plat']
            day_comm = day_b2c - day_plat
            day_b2b = b2b_by_date.get(m.date, Decimal('0.00'))
            day_tokens = tokens_by_date.get(m.date, 0)
            day_gross = day_b2c + day_b2b
            day_net = day_plat + day_b2b

            writer.writerow([
                m.date,
                f"{day_gross:.2f}",
                f"{day_net:.2f}",
                f"{day_b2c:.2f}",
                f"{day_b2b:.2f}",
                f"{day_comm:.2f}",
                day_tokens,
            ])

        return response
