
import os
import django
import sys
from django.core.management import call_command
from datetime import timedelta
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def backfill():
    print("Backfilling analytics for the last 30 days...")
    today = timezone.now().date()
    
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        print(f"Processing {date_str}...")
        try:
            call_command('calculate_metrics', date=date_str)
        except Exception as e:
            print(f"Error for {date_str}: {e}")

backfill()
