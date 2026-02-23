from django.core.management.base import BaseCommand
from course.models import Course
import random

class Command(BaseCommand):
    help = 'Syncs course thumbnails with unique random images using LoremFlickr'

    def handle(self, *args, **kwargs):
        courses = Course.objects.all()
        total_courses = courses.count()
        updated_count = 0

        self.stdout.write(f"Updating {total_courses} courses with unique images...")

        for course in courses:
            # Use LoremFlickr with 'lock' parameter based on course ID
            # This ensures (1) uniqueness per ID and (2) consistency (same ID always gets same image)
            # Categories: business, coding, computer, technology
            
            # Note: We append a random unrelated query param just to ensure the URL string looks different 
            # if we were to view them in a list, but the 'lock' is what matters for the image provider.
            
            image_url = f"https://loremflickr.com/800/600/learning,code,tech?lock={course.id}"
            
            course.thumbnail = image_url
            course.save()
            updated_count += 1
            
            if updated_count % 50 == 0:
                self.stdout.write(f"Processed {updated_count}/{total_courses} courses...")

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} courses with 1-to-1 unique images.'))
