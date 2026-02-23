
import os
import django
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Is Staff'}")
print("-" * 70)
for user in User.objects.all():
    print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.is_staff}")
