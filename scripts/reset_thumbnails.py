
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from course.models import Course

TARGET_SLUGS = [
    "machine-learning-mastery-level-4",
    "deep-learning-mastery-level-3",
    "business-strategy-mastery-level-4"
]

def run():
    print("🔄 Resetting Course Thumbnails...")
    
    for slug in TARGET_SLUGS:
        try:
            course = Course.objects.get(slug=slug)
            print(f"  Found course: {course.title}")
            print(f"  ID: {course.id}")
            print(f"  Current Thumbnail: {course.thumbnail}")
            
            # Clear thumbnail
            course.thumbnail = None
            course.save()
            print("  ✅ Thumbnail cleared.")
                
        except Course.DoesNotExist:
            print(f"  ⚠️ Course not found: {slug}")

if __name__ == "__main__":
    run()
