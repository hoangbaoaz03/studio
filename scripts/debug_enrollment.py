
import os
import sys
import django
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from course.models import Course
from result.serializers import EnrollmentSerializer

def run():
    print("🛠 Debugging Enrollment 500 Error...")
    User = get_user_model()
    
    # Get a test user
    try:
        user = User.objects.first()
        if not user:
            print("No users found! Create a user first.")
            return
        print(f"User: {user.username} (ID: {user.id})")
    except Exception as e:
        print(f"Error getting user: {e}")
        return

    # Get a course
    try:
        course = Course.objects.first()
        if not course:
            print("No courses found!")
            return
        print(f"Course: {course.title} (ID: {course.id})")
    except Exception as e:
        print(f"Error getting course: {e}")
        return

    # Simulate Enrollment
    data = {'course': course.id}
    print(f"Payload: {data}")
    
    serializer = EnrollmentSerializer(data=data)
    if serializer.is_valid():
        print("Serializer is valid.")
        try:
            print("Attempting save...")
            serializer.save(student=user)
            print("✅ Enrollment saved successfully!")
        except Exception:
            print("❌ CRASH DURING SAVE:")
            traceback.print_exc()
    else:
        print("❌ Serializer Validation Error:")
        print(serializer.errors)

if __name__ == "__main__":
    run()
