
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

def reset_pass(username, password):
    try:
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_staff = True
        u.is_superuser = True
        u.save()
        print(f"Reset password for '{username}' to '{password}' and ensured Admin privileges.")
    except User.DoesNotExist:
        print(f"User '{username}' does not exist.")

reset_pass('dr_angela', 'password123')

# Check if admin exists, if not create
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Created superuser 'admin' with password 'admin123'")
else:
    reset_pass('admin', 'admin123')
