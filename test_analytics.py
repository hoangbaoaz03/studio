import os, sys, django
os.chdir(r'e:\LapTrinhweb\DOAN\DOAN\doan')
sys.path.insert(0, r'e:\LapTrinhweb\DOAN\DOAN\doan')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

import datetime, traceback
from decimal import Decimal

try:
    from analytics.views import _get_date_range, _aggregate_transactions, _aggregate_b2b, _aggregate_tokens
    start_date, end_date = _get_date_range('30d')
    print('date range OK:', start_date, end_date)
    
    b2c, fee, comm, tx_dict = _aggregate_transactions(start_date, end_date)
    print('transactions OK: b2c=%s fee=%s comm=%s' % (b2c, fee, comm))
    
    b2b, b2b_dict = _aggregate_b2b(start_date, end_date)
    print('b2b OK:', b2b)
    
    tokens, tok_dict = _aggregate_tokens(start_date, end_date)
    print('tokens OK:', tokens)
    
    from analytics.models import DailyMetric
    daily = list(DailyMetric.objects.filter(date__range=(start_date, end_date)).order_by('date'))
    print('daily_metrics count:', len(daily))
    
    from course.models import Course
    courses = Course.objects.filter(status='published').count()
    print('courses OK:', courses)
    
    summary_data = {
        'gross_revenue': float(b2c + b2b),
        'net_revenue': float(fee + b2b),
        'b2c_revenue': float(b2c),
        'b2b_revenue': float(b2b),
        'instructor_commission': float(comm),
        'ai_tokens_used': int(tokens),
        'total_users': int(daily[-1].total_users if daily else 0),
        'active_courses': int(courses),
    }
    print('summary OK:', summary_data)

    trend_data = []
    for m in daily:
        d = tx_dict.get(m.date, {'rev': Decimal('0'), 'plat': Decimal('0')})
        trend_data.append({
            'date': m.date,
            'revenue': float(d['rev']) + float(b2b_dict.get(m.date, Decimal('0'))),
            'b2c_revenue': float(d['rev']),
            'b2b_revenue': float(b2b_dict.get(m.date, Decimal('0'))),
            'ai_tokens_used': tok_dict.get(m.date, 0),
            'new_users': m.new_users,
        })
    print('trend_data count:', len(trend_data))
    
    from analytics.serializers import DashboardAnalyticsSerializer
    full_data = {'summary': summary_data, 'trend': trend_data, 'top_courses': [], 'category_distribution': []}
    ser = DashboardAnalyticsSerializer(full_data)
    print('serializer data keys:', list(ser.data.keys()))
    print('=== ALL OK ===')

except Exception as e:
    print('ERROR:', str(e))
    traceback.print_exc()
