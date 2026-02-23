import os
import sys
import django
import random
from django.utils.text import slugify

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from course.models import Category, Course
from accounts.models import User

def run():
    print("📚 Starting Course Population...")
    
    # Get an instructor
    instructor = User.objects.filter(is_instructor=True).first()
    if not instructor:
        print("❌ No instructor found! Please create one first.")
        return

    # Get all categories
    categories = Category.objects.all()
    
    total_added = 0
    
    for cat in categories:
        # Check current course count (including descendants)
        # But for population, we should probably add to the leaf node directly
        # or just add to this specific category if it's a leaf?
        # User said "add at least 5 courses to EACH category".
        
        # Simple check: direct courses
        current_count = Course.objects.filter(category=cat).count()
        missing = 5 - current_count
        
        if missing > 0:
            print(f"  Category '{cat.name}' has {current_count} courses. Adding {missing}...")
            
            for i in range(missing):
                title = f"{cat.name} Mastery: Level {i+1}"
                Course.objects.create(
                    instructor=instructor,
                    category=cat,
                    title=title,
                    subtitle=f"Complete guide to {cat.name} for beginners",
                    description=f"Learn {cat.name} from scratch...",
                    price=19.99,
                    status='published',
                    level='beginner',
                    language='English'
                )
                total_added += 1
                
    print(f"\n✅ Added {total_added} new courses across all categories.")

if __name__ == "__main__":
    run()
