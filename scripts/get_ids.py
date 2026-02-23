
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
    print("--- ID Lookup ---")
    for slug in TARGET_SLUGS:
        try:
            course = Course.objects.get(slug=slug)
            print(f"Slug: {slug} | ID: {course.id}")
        except Course.DoesNotExist:
            print(f"Slug: {slug} | Not Found")

if __name__ == "__main__":
    run()
