"""
Add more courses to fill all categories
"""
import os
import sys
import django
from decimal import Decimal
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from course.models import Category, Subcategory, Course, Section, Lecture
from accounts.models import InstructorProfile

User = get_user_model()

# Additional courses for empty categories
ADDITIONAL_COURSES = [
    # Business courses
    {
        "instructor_username": "jose_portilla",
        "category": "Business",
        "subcategory": "Entrepreneurship",
        "title": "The Complete Business Plan Course",
        "subtitle": "Learn how to write a business plan to start and grow your business. Includes templates and examples!",
        "price": Decimal("79.99"),
        "discount_price": Decimal("15.99"),
        "level": "all",
        "average_rating": 4.5,
        "total_reviews": 12500,
        "total_enrollments": 65000,
    },
    {
        "instructor_username": "colt_steele",
        "category": "Business",
        "subcategory": "Communication",
        "title": "Complete Communication Skills Master Class",
        "subtitle": "Communication Skills, Presentation Skills, Negotiation, Public Speaking & Business Writing in One Course",
        "price": Decimal("89.99"),
        "discount_price": Decimal("16.99"),
        "level": "all",
        "average_rating": 4.6,
        "total_reviews": 8700,
        "total_enrollments": 42000,
    },
    # Design courses
    {
        "instructor_username": "maximilian",
        "category": "Design",
        "subcategory": "Web Design",
        "title": "Web Design for Beginners: Real World Coding in HTML & CSS",
        "subtitle": "Launch a career as a web designer by learning HTML5, CSS3, responsive design, Sass and more!",
        "price": Decimal("84.99"),
        "discount_price": Decimal("17.99"),
        "level": "beginner",
        "average_rating": 4.7,
        "total_reviews": 23400,
        "total_enrollments": 120000,
    },
    {
        "instructor_username": "stephen_grider",
        "category": "Design",
        "subcategory": "UX Design",
        "title": "Complete UI/UX Design: From Beginner to Expert",
        "subtitle": "Master UI/UX design using Figma. Learn design theory, user research, wireframing and prototyping.",
        "price": Decimal("94.99"),
        "discount_price": Decimal("18.99"),
        "level": "all",
        "average_rating": 4.6,
        "total_reviews": 15600,
        "total_enrollments": 85000,
    },
    {
        "instructor_username": "dr_angela",
        "category": "Design",
        "subcategory": "Graphic Design",
        "title": "Graphic Design Masterclass: Intermediate",
        "subtitle": "Learn Graphic Design Theory and Projects. Use Photoshop, Illustrator & InDesign",
        "price": Decimal("74.99"),
        "discount_price": Decimal("14.99"),
        "level": "intermediate",
        "average_rating": 4.5,
        "total_reviews": 9800,
        "total_enrollments": 55000,
    },
    # Marketing courses
    {
        "instructor_username": "jose_portilla",
        "category": "Marketing",
        "subcategory": "Digital Marketing",
        "title": "The Complete Digital Marketing Course - 12 Courses in 1",
        "subtitle": "Master Digital Marketing Strategy, Social Media Marketing, SEO, YouTube, Email, Facebook Marketing, Analytics & More!",
        "price": Decimal("99.99"),
        "discount_price": Decimal("19.99"),
        "level": "all",
        "average_rating": 4.5,
        "total_reviews": 87000,
        "total_enrollments": 450000,
    },
    {
        "instructor_username": "colt_steele",
        "category": "Marketing",
        "subcategory": "SEO",
        "title": "SEO 2024: Complete SEO Training + SEO for WordPress Websites",
        "subtitle": "Master SEO best practices, keyword research, link building, and local SEO to rank #1 on Google",
        "price": Decimal("69.99"),
        "discount_price": Decimal("13.99"),
        "level": "all",
        "average_rating": 4.4,
        "total_reviews": 25000,
        "total_enrollments": 130000,
    },
    {
        "instructor_username": "maximilian",
        "category": "Marketing",
        "subcategory": "Social Media Marketing",
        "title": "Social Media Marketing MASTERY | Learn Ads on 10+ Platforms",
        "subtitle": "Master Social Media Marketing on Facebook, Instagram, TikTok, LinkedIn, Twitter & More",
        "price": Decimal("79.99"),
        "discount_price": Decimal("15.99"),
        "level": "all",
        "average_rating": 4.5,
        "total_reviews": 18700,
        "total_enrollments": 95000,
    },
]

def run():
    print("🌱 Adding additional courses...")

    for course_data in ADDITIONAL_COURSES:
        try:
            instructor = User.objects.get(username=course_data["instructor_username"])
        except User.DoesNotExist:
            print(f"  ⚠️ Instructor not found: {course_data['instructor_username']}")
            continue
            
        try:
            category = Category.objects.get(name=course_data["category"])
        except Category.DoesNotExist:
            print(f"  ⚠️ Category not found: {course_data['category']}")
            continue
            
        subcategory, _ = Subcategory.objects.get_or_create(
            category=category,
            name=course_data["subcategory"]
        )
        
        slug = course_data["title"].lower()
        for char in ":'&+()[]":
            slug = slug.replace(char, "")
        slug = slug.replace(" ", "-")[:80]
        
        course, created = Course.objects.get_or_create(
            slug=slug,
            defaults={
                "instructor": instructor,
                "title": course_data["title"],
                "subtitle": course_data["subtitle"],
                "category": category,
                "subcategory": subcategory,
                "description": f"{course_data['subtitle']}\n\nComprehensive course by {instructor.get_full_name()}.",
                "price": course_data["price"],
                "discount_price": course_data["discount_price"],
                "level": course_data["level"],
                "language": "English",
                "status": "published",
                "average_rating": course_data["average_rating"],
                "total_reviews": course_data["total_reviews"],
                "total_enrollments": course_data["total_enrollments"],
                "what_you_will_learn": [
                    f"Master {course_data['subcategory']} concepts",
                    "Build real-world projects",
                    f"Learn from {instructor.get_full_name()}",
                ],
                "requirements": ["No prior experience needed"],
            }
        )
        
        if created:
            print(f"  ✅ Created: {course.title}")
            
            # Add sections
            for i, sec_title in enumerate(["Getting Started", "Core Concepts", "Advanced Topics"], 1):
                section = Section.objects.create(course=course, title=sec_title, order=i)
                for j in range(1, 5):
                    Lecture.objects.create(
                        section=section,
                        title=f"Lecture {j}",
                        order=j,
                        duration=random.randint(300, 900),
                        is_preview=(j == 1 and i == 1)
                    )
            course.update_stats()
        else:
            print(f"  ⏭️ Exists: {course.title}")

    # Print summary
    print("\n📊 Category Summary:")
    for cat in Category.objects.all():
        count = Course.objects.filter(category=cat).count()
        print(f"   {cat.name}: {count} courses")

if __name__ == "__main__":
    run()
