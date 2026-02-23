
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = "dr_angela" # Target user
try:
    user = User.objects.get(username=username)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"Successfully promoted {username} to Staff/Superuser")
except User.DoesNotExist:
    print(f"User {username} not found. Creating 'admin' user instead.")
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            print("Created superuser 'admin' with password 'admin'")
        else:
            u = User.objects.get(username='admin')
            u.set_password('admin')
            u.save()
            print("Reset password for 'admin' to 'admin'")
    except Exception as e:
        print(f"Error: {e}")
