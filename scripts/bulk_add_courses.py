"""
Bulk add many courses to make the platform look more like Udemy
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

# Course templates by category
COURSE_TEMPLATES = {
    "Development": [
        ("JavaScript - The Complete Guide 2024", "From Beginner to Expert! Modern JavaScript from the start - all the way up to JS expert level!", "beginner"),
        ("Node.js - The Complete Guide (MVC, REST APIs, GraphQL)", "Master Node.js by building a real-world RESTful API and web application", "intermediate"),
        ("Angular - The Complete Guide (2024 Edition)", "Master Angular including Standalone Components, Signals, RxJS and more!", "intermediate"),
        ("Vue - The Complete Guide (incl. Router & Composition API)", "Vue.js is an awesome JavaScript Framework for building Frontend Applications!", "intermediate"),
        ("TypeScript: The Complete Developer's Guide", "Master TypeScript by learning popular design patterns and building complex projects", "intermediate"),
        ("Go: The Complete Developer's Guide (Golang)", "Master the fundamentals and advanced features of the Go Programming Language", "beginner"),
        ("Rust Programming: The Complete Developer's Guide", "Learn Rust from scratch and build blazingly fast applications", "intermediate"),
        ("AWS Certified Solutions Architect Associate 2024", "Pass the AWS Certified Solutions Architect Associate Certification", "intermediate"),
        ("Machine Learning A-Z: AI, Python & R", "Learn to create Machine Learning Algorithms in Python and R from two Data Science experts", "intermediate"),
        ("Deep Learning A-Z 2024: Neural Networks, AI & ChatGPT", "Learn to create Deep Learning Algorithms in Python from two Machine Learning experts", "advanced"),
    ],
    "Business": [
        ("The Complete MBA Masterclass: Business Strategy", "Learn business fundamentals, strategy, management & more", "all"),
        ("Financial Analyst Complete Training", "Become a professional financial analyst", "intermediate"),
        ("Project Management Professional (PMP)", "Prepare for the PMP certification exam", "intermediate"),
        ("Leadership: Practical Leadership Skills", "Master leadership skills for your career", "all"),
        ("Agile Scrum Master Certification", "Become a Scrum Master with practical training", "beginner"),
        ("Excel Skills for Business: Essentials", "Master Microsoft Excel from beginner to advanced", "beginner"),
        ("Entrepreneurship: How to Start a Business", "Learn the complete process to start your own business", "beginner"),
        ("Supply Chain Management Fundamentals", "Master supply chain logistics and operations", "intermediate"),
    ],
    "Design": [
        ("Adobe Photoshop CC: The Complete Guide", "Master Photoshop from scratch with practical projects", "beginner"),
        ("Adobe Illustrator CC - Essentials Training", "Learn Adobe Illustrator from the ground up", "beginner"),
        ("Figma UI/UX Design Essentials", "Learn Figma for UI/UX design from scratch", "beginner"),
        ("Motion Graphics and VFX in After Effects", "Create stunning motion graphics and visual effects", "intermediate"),
        ("3D Modeling in Blender", "Learn 3D modeling, texturing and rendering in Blender", "beginner"),
        ("Logo Design Mastery: The Full Course", "Master logo design principles and techniques", "beginner"),
        ("Character Design for Animation", "Learn to design memorable characters for animation", "intermediate"),
    ],
    "Marketing": [
        ("Google Ads (AdWords) Complete Course", "Master Google Ads from beginner to advanced", "all"),
        ("Facebook Ads & Meta Marketing MASTERY", "Create profitable Facebook and Instagram ad campaigns", "all"),
        ("Content Marketing Strategy Complete Guide", "Build an effective content marketing strategy", "intermediate"),
        ("Email Marketing Masterclass", "Master email marketing and build your list", "beginner"),
        ("TikTok Marketing: Complete Guide 2024", "Master TikTok marketing for business growth", "beginner"),
        ("Copywriting Secrets: Write Text That Sells", "Learn persuasive copywriting techniques", "beginner"),
        ("Influencer Marketing Strategy", "Build and execute influencer marketing campaigns", "intermediate"),
    ],
    "IT & Software": [
        ("Linux Mastery: Master the Linux Command Line", "Learn Linux administration from scratch", "beginner"),
        ("CompTIA Security+ SY0-701 Complete Course", "Prepare for the CompTIA Security+ certification", "intermediate"),
        ("Ethical Hacking & Penetration Testing", "Learn ethical hacking and cybersecurity skills", "intermediate"),
        ("Kubernetes for the Absolute Beginners", "Learn Kubernetes in simple, easy and fun way", "beginner"),
        ("Terraform for DevOps: Beginner to Expert", "Master Infrastructure as Code with Terraform", "intermediate"),
        ("Windows Server Administration Fundamentals", "Learn Windows Server administration", "beginner"),
        ("Git & GitHub Complete Masterclass", "Master version control and collaboration", "beginner"),
    ],
    "Finance & Accounting": [
        ("Accounting & Bookkeeping Masterclass", "Learn accounting fundamentals and bookkeeping", "beginner"),
        ("Stock Market Investing for Beginners", "Learn to invest in the stock market", "beginner"),
        ("Cryptocurrency & Bitcoin Trading 2024", "Master cryptocurrency trading strategies", "intermediate"),
        ("Financial Modeling in Excel", "Build professional financial models in Excel", "intermediate"),
        ("Personal Finance & Budgeting Bootcamp", "Take control of your personal finances", "beginner"),
        ("Real Estate Investing from A to Z", "Learn real estate investment strategies", "beginner"),
    ],
}

def create_slug(title):
    slug = title.lower()
    for char in ":'&+()[]!,-":
        slug = slug.replace(char, "")
    slug = slug.replace(" ", "-")[:80]
    return slug

def run():
    print("🌱 Bulk adding courses...")
    
    instructors = list(User.objects.filter(is_instructor=True))
    if not instructors:
        print("❌ No instructors found! Run seed_udemy_data.py first.")
        return
    
    total_created = 0
    
    for cat_name, course_list in COURSE_TEMPLATES.items():
        try:
            category = Category.objects.get(name=cat_name)
        except Category.DoesNotExist:
            print(f"  ⚠️ Category not found: {cat_name}")
            continue
        
        subcategories = list(Subcategory.objects.filter(category=category))
        if not subcategories:
            subcategory, _ = Subcategory.objects.get_or_create(category=category, name="General")
            subcategories = [subcategory]
        
        for title, subtitle, level in course_list:
            instructor = random.choice(instructors)
            subcategory = random.choice(subcategories)
            slug = create_slug(title)
            
            course, created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "instructor": instructor,
                    "title": title,
                    "subtitle": subtitle,
                    "category": category,
                    "subcategory": subcategory,
                    "description": f"{subtitle}\n\nThis comprehensive course covers everything you need to know about {title.split(':')[0].split('-')[0].strip()}.",
                    "price": Decimal(str(random.choice([79.99, 84.99, 89.99, 94.99]))),
                    "discount_price": Decimal(str(random.choice([12.99, 14.99, 16.99, 18.99, 19.99]))),
                    "level": level,
                    "language": "English",
                    "status": "published",
                    "average_rating": round(random.uniform(4.3, 4.9), 1),
                    "total_reviews": random.randint(5000, 200000),
                    "total_enrollments": random.randint(20000, 800000),
                    "what_you_will_learn": [
                        f"Master {title.split(':')[0].split('-')[0].strip()}",
                        "Build real-world projects",
                        "Learn best practices",
                        "Get hands-on experience"
                    ],
                    "requirements": ["Basic computer skills", "Willingness to learn"],
                }
            )
            
            if created:
                total_created += 1
                # Add sections
                sections_titles = ["Introduction", "Fundamentals", "Intermediate Concepts", "Advanced Topics", "Projects"]
                for i, sec_title in enumerate(sections_titles, 1):
                    section = Section.objects.create(course=course, title=sec_title, order=i)
                    for j in range(1, random.randint(3, 8)):
                        Lecture.objects.create(
                            section=section,
                            title=f"Lecture {j}: {sec_title} Part {j}",
                            order=j,
                            duration=random.randint(300, 1200),
                            is_preview=(i == 1 and j == 1)
                        )
                course.update_stats()
    
    print(f"\n✅ Created {total_created} new courses!")
    
    # Print summary
    print("\n📊 Category Summary:")
    for cat in Category.objects.all():
        count = Course.objects.filter(category=cat).count()
        print(f"   {cat.name}: {count} courses")
    
    print(f"\n🎯 Total courses: {Course.objects.count()}")

if __name__ == "__main__":
    run()
