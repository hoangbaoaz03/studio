
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

with open("ids.txt", "w") as f:
    for slug in TARGET_SLUGS:
        try:
            course = Course.objects.get(slug=slug)
            f.write(f"{slug}|{course.id}\n")
        except Course.DoesNotExist:
            f.write(f"{slug}|NOT_FOUND\n")
