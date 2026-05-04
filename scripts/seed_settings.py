
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import SystemKey

DEFAULTS = [
    {
        'key': 'site_maintenance_mode',
        'value': 'false',
        'type': 'bool',
        'description': 'Enable to block non-admin access',
        'is_public': True
    },
    {
        'key': 'platform_fee_percent',
        'value': '15.0',
        'type': 'float',
        'description': 'Commission percentage needed from course sales',
        'is_public': False
    },
    {
        'key': 'support_email',
        'value': 'support@studigo.com',
        'type': 'string',
        'description': 'Contact email displayed in footer',
        'is_public': True
    },
    {
        'key': 'feature_flags',
        'value': '{"new_checkout": true, "ai_recommendations": false}',
        'type': 'json',
        'description': 'Toggle beta features',
        'is_public': False
    }
]

def seed():
    print("Seeding settings...")
    for item in DEFAULTS:
        obj, created = SystemKey.objects.get_or_create(
            key=item['key'],
            defaults=item
        )
        if created:
            print(f"Created {item['key']}")
        else:
            print(f"Skipped {item['key']} (exists)")

seed()
