import os
import sys
import django
import random
import uuid
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from course.models import Course, Section, Lecture
from result.models import Enrollment, Review
from accounts.models import User

# Sample Data
DESCRIPTIONS = [
    "This comprehensive course covers everything you need to know about this topic. From basics to advanced concepts, we guide you through step-by-step.",
    "Master this skill in record time. Designed for beginners and professionals alike, this course is practical, hands-on, and up-to-date.",
    "Unlock your potential with our expert-led training. Dive deep into real-world scenarios and build a portfolio-ready project by the end.",
    "Join thousands of students in learning the most in-demand skills in the industry. Updated for 2026 with the latest best practices."
]

TITLES_SECTION = ["Introduction", "Getting Started", "Core Concepts", "Advanced Techniques", "Project Work", "Conclusion"]
TITLES_LECTURE = ["Welcome to the Course", "Setting Up Your Environment", "Understanding the Basics", "Deep Dive into Theory", "Practical Example", "Tips and Tricks", "Final Review"]

REVIEW_COMMENTS = [
    ("Amazing course! Highly recommended.", 5),
    ("Very good content, clear explanations.", 4),
    ("Good, but could go faster.", 4),
    ("Solid introduction for beginners.", 5),
    ("Expected more depth on advanced topics.", 3),
    ("Instructor is knowledgeable but audio is okay.", 4),
    ("Best course I've taken on this subject!", 5),
    ("Changed my career path. Thank you!", 5),
    ("A bit outdated in some parts.", 3),
    ("Excellent value for money.", 5)
]

def create_students(count=10):
    """Ensure we have enough dummy students"""
    students = []
    for i in range(count):
        username = f"student_{i+100}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@example.com", 
                'first_name': f"Student", 
                'last_name': f"{i+100}"
            }
        )
        if created:
            user.set_password("password123")
            user.save()
        students.append(user)
    return students

def run():
    print("🚀 Starting Course Enrichment...")
    
    courses = Course.objects.all()
    students = create_students(20)
    
    for course in courses:
        print(f"Processing: {course.title}")
        
        # 1. Enrich Description & Metadata
        if len(course.description) < 50:
            course.description = random.choice(DESCRIPTIONS) + f"\n\nIn this course on {course.title}, you will learn fundamentals and advanced strategies."
        
        if not course.what_you_will_learn:
             course.what_you_will_learn = [
                 f"Master the fundamentals of {course.title}",
                 "Build real-world projects",
                 "Understand best practices and common pitfalls",
                 "Prepare for job interviews"
             ]
             
        if not course.requirements:
             course.requirements = ["No prior experience needed", "A computer with internet access"]
             
        if not course.target_audience:
             course.target_audience = ["Beginners", "Students", "Professionals looking to upskill"]
             
        # 2. Ensure Sections & Lectures
        if course.sections.count() == 0:
            print("  - Adding sections and lectures...")
            for i, sec_title in enumerate(TITLES_SECTION[:random.randint(3, 6)]):
                section = Section.objects.create(course=course, title=sec_title, order=i)
                
                # Add 3-5 lectures per section
                for j in range(random.randint(3, 5)):
                    lecture_title = f"{random.choice(TITLES_LECTURE)} - Part {j+1}"
                    Lecture.objects.create(
                        section=section,
                        title=lecture_title,
                        order=j,
                        duration=random.randint(300, 1200), # 5-20 mins
                        is_preview=(i==0 and j==0) # First lecture is free
                    )
        
        # 3. Add Enrollments (Students)
        current_enrollments = course.enrollments.count()
        target_enrollments = random.randint(5, 50)
        
        if current_enrollments < 5:
            print("  - Adding students...")
            # Enroll random students
            potential_students = [s for s in students if not Enrollment.objects.filter(student=s, course=course).exists()]
            to_enroll = random.sample(potential_students, k=min(len(potential_students), target_enrollments - current_enrollments))
            
            for student in to_enroll:
                try:
                    # Check if already enrolled
                    if not Enrollment.objects.filter(student=student, course=course).exists():
                        Enrollment.objects.create(
                            student=student,
                            course=course,
                            price_paid=course.price if not course.is_free else 0,
                            certificate_number=str(uuid.uuid4()) # Unique ID
                        )
                except Exception as e:
                    print(f"    ⚠️ Failed to enroll {student.username}: {e}")
        
        # 4. Add Reviews & Ratings
        try:
            current_reviews = course.reviews.count()
            if current_reviews < 3:
                print("  - Adding reviews...")
                # Get enrolled students
                enrolled_students = [e.student for e in course.enrollments.all()]
                # Filter those who haven't reviewed yet
                potential_reviewers = [s for s in enrolled_students if not Review.objects.filter(student=s, course=course).exists()]
                
                to_review = random.sample(potential_reviewers, k=min(len(potential_reviewers), random.randint(3, 8)))
                
                for student in to_review:
                    comment, rating = random.choice(REVIEW_COMMENTS)
                    # Add some randomness to rating
                    if random.random() > 0.8: rating = max(1, rating - 1)
                    
                    enrollment = Enrollment.objects.get(student=student, course=course)
                    Review.objects.create(
                        student=student,
                        course=course,
                        enrollment=enrollment,
                        rating=rating,
                        comment=comment,
                        title="Great course!"
                    )
        except Exception as e:
            print(f"    ⚠️ Failed to add reviews: {e}")
        
        # Recalculate stats
        course.update_stats()
        course.save()

    print("\n✅ Course enrichment complete!")

if __name__ == "__main__":
    run()
