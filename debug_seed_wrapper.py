
import os
import django
import sys
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from scripts.seed_financials import seed
    seed()
except Exception:
    traceback.print_exc()
