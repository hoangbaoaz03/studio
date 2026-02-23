
import os
import sys
import django
import requests
from django.core.files.base import ContentFile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from course.models import Course

IMAGE_MAPPINGS = {
    "machine-learning-mastery-level-4": "https://images.unsplash.com/photo-1593642532744-d377ab507dc8?auto=format&fit=crop&q=80&w=800",
    "deep-learning-mastery-level-3": "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?auto=format&fit=crop&q=80&w=800",
    "business-strategy-mastery-level-4": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&q=80&w=800"
}

def run():
    print("🔄 Synchronizing Course Images...")
    
    for slug, url in IMAGE_MAPPINGS.items():
        try:
            course = Course.objects.get(slug=slug)
            print(f"  Found course: {course.title} ({slug})")
            
            if not course.thumbnail:
                print(f"  Downloading image from {url}...")
                response = requests.get(url)
                if response.status_code == 200:
                    file_name = f"{slug}.jpg"
                    course.thumbnail.save(file_name, ContentFile(response.content), save=True)
                    print("  ✅ Image saved!")
                else:
                    print(f"  ❌ Failed to download image: {response.status_code}")
            else:
                print("  ℹ️ Image already exists, skipping.")
                
        except Course.DoesNotExist:
            print(f"  ⚠️ Course not found: {slug}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    run()
