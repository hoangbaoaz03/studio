
import os
import django
import sys
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from course.models import Course
from reports.models import Report

User = get_user_model()

def seed():
    print("Seeding reports...")
    users = list(User.objects.all())
    courses = list(Course.objects.all())
    
    if not users or not courses:
        print("No users or courses found")
        return

    course_type = ContentType.objects.get_for_model(Course)
    
    reasons = ['spam', 'inappropriate', 'other', 'copyright']
    
    # Create 5 open reports
    for i in range(5):
        Report.objects.create(
            reporter=random.choice(users),
            content_type=course_type,
            object_id=random.choice(courses).id,
            reason=random.choice(reasons),
            description=f"This is a test report description {i}",
            status='open'
        )
        print(f"Created open report {i}")
        
    # Create 3 resolved
    for i in range(3):
        r = Report.objects.create(
            reporter=random.choice(users),
            content_type=course_type,
            object_id=random.choice(courses).id,
            reason=random.choice(reasons),
            description="Resolved report",
            status='resolved'
        )
        print(f"Created resolved report {i}")

seed()
