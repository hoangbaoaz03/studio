"""
Update courses with placeholder thumbnails from Unsplash
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from course.models import Course, Category

# Unsplash images by category
CATEGORY_IMAGES = {
    "Development": [
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1607706189992-eae578626c86?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1537432376149-e84978a29c4f?w=600&h=400&fit=crop",
    ],
    "Business": [
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1553484771-371a605b060b?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=600&h=400&fit=crop",
    ],
    "Design": [
        "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1558655146-9f40138edfeb?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1609921212029-bb5a28e60960?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1626785774573-4b799315345d?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1572044162444-ad60f128bdea?w=600&h=400&fit=crop",
    ],
    "Marketing": [
        "https://images.unsplash.com/photo-1533750349088-cd871a92f312?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1557838923-2985c318be48?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1432888498266-38ffec3eaf0a?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1611926653458-09294b3142bf?w=600&h=400&fit=crop",
    ],
    "IT & Software": [
        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1510915228340-29c85a43dcfe?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&h=400&fit=crop",
    ],
    "Finance & Accounting": [
        "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1518458028785-8fbcd101ebb9?w=600&h=400&fit=crop",
        "https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?w=600&h=400&fit=crop",
    ],
}

def run():
    print("🖼️ Updating course thumbnails...")
    
    updated = 0
    for category in Category.objects.all():
        images = CATEGORY_IMAGES.get(category.name, CATEGORY_IMAGES.get("Development", []))
        courses = Course.objects.filter(category=category)
        
        for i, course in enumerate(courses):
            if images:
                image_url = images[i % len(images)]
                # Note: We can't directly save URLs to ImageField
                # We'll update the frontend to use external URLs properly
                print(f"  📷 {course.title[:50]}... -> Image #{(i % len(images)) + 1}")
        
        updated += courses.count()
    
    print(f"\n✅ Processed {updated} courses")
    print("\n⚠️ Note: Django ImageField doesn't support external URLs directly.")
    print("   The frontend will use placeholder images from the code.")

if __name__ == "__main__":
    run()
