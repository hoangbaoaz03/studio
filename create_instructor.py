import os
import django
import sys

# Setup Django environment
# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doan.config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doan.accounts.models import InstructorProfile

User = get_user_model()

def create_instructor():
    username = 'instructor'
    email = 'instructor@example.com'
    password = 'password123'
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists.")
        user = User.objects.get(username=username)
    else:
        user = User.objects.create_user(username=username, email=email, password=password)
        print(f"User '{username}' created.")

    # Update attributes
    user.first_name = "Test"
    user.last_name = "Instructor"
    user.is_instructor = True
    user.save()
    
    # Ensure profile exists
    if not hasattr(user, 'instructor_profile'):
        InstructorProfile.objects.create(user=user, about="I am a test instructor.")
        print("Instructor profile created.")
    else:
        print("Instructor profile already exists.")
        
    print(f"\nLogin Details:\nUsername: {username}\nPassword: {password}")

if __name__ == '__main__':
    create_instructor()
