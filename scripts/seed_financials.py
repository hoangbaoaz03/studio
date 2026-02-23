
import os
import django
import sys
import random
from decimal import Decimal
from django.utils import timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from course.models import Course
from result.models import Enrollment
from payments.models import Transaction, InstructorPayout

User = get_user_model()

def seed():
    print("Seeding financial data...")
    courses = list(Course.objects.all())
    students = list(User.objects.filter(is_instructor=False))
    instructors = list(User.objects.filter(is_instructor=True))

    if not courses or not students:
        print("Need courses and students to seed transactions.")
        return

    # 1. Create Transactions
    for _ in range(20):
        student = random.choice(students)
        course = random.choice(courses)
        
        # Ensure enrollment exists
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course
        )
        
        # Check if txn exists
        if not Transaction.objects.filter(enrollment=enrollment).exists():
            gross = course.price if course.price else Decimal('19.99')
            if gross == 0: gross = Decimal('9.99')
            
            Transaction.objects.create(
                transaction_id=f"txn_{random.randint(10000,99999)}_{course.id}",
                enrollment=enrollment,
                student=student,
                course=course,
                gross_amount=gross,
                platform_fee_percent=Decimal('15.00'),
                payment_method=random.choice(['stripe', 'paypal', 'momo']),
                status=random.choice(['completed', 'completed', 'completed', 'failed']),
                created_at=timezone.now() - timezone.timedelta(days=random.randint(1, 30))
            )
            print(f"Created txn for {course.title}")

    # 2. Create Payout Requests
    for instructor in instructors:
        # Check if payout exists for this month
        if not InstructorPayout.objects.filter(
            instructor=instructor, 
            period_year=2025, 
            period_month=1
        ).exists():
            InstructorPayout.objects.create(
                instructor=instructor,
                period_year=2025,
                period_month=1,
                total_revenue=Decimal('500.00'),
                platform_fee=Decimal('75.00'),
                payout_amount=Decimal('425.00'),
                status='pending'
            )
            print(f"Created pending payout for {instructor.username}")
            
        # Create a paid one for last month
        if not InstructorPayout.objects.filter(
            instructor=instructor, 
            period_year=2024, 
            period_month=12
        ).exists():
            InstructorPayout.objects.create(
                instructor=instructor,
                period_year=2024,
                period_month=12,
                total_revenue=Decimal('1000.00'),
                platform_fee=Decimal('150.00'),
                payout_amount=Decimal('850.00'),
                status='paid',
                paid_at=timezone.now() - timezone.timedelta(days=20)
            )
            print(f"Created paid payout for {instructor.username}")

seed()
