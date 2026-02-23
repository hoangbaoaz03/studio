
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
from payments.models import Transaction

User = get_user_model()

def run():
    print("Start debug...")
    try:
        user = User.objects.first()
        course = Course.objects.first()
        if not user or not course:
            print("No user/course")
            return

        print(f"User: {user}, Course: {course}")
        
        # Check model fields
        print("Transaction Fields:", [f.name for f in Transaction._meta.get_fields()])
        
        # Test basic query (checks ordering)
        try:
            print("Count all:", Transaction.objects.all().count())
        except Exception as e:
            print("Count all failed:", e)

        # Test query without ordering
        try:
            print("Count unordered:", Transaction.objects.order_by().count())
        except Exception as e:
            print("Count unordered failed:", e)

        enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
        print(f"Enrollment: {enrollment.id}")
        
        # Try simple filter
        exists = Transaction.objects.filter(enrollment=enrollment).exists()
        print(f"Exists check: {exists}")
        
        if not exists:
            print("Creating transaction...")
            t = Transaction.objects.create(
                transaction_id=f"debug_{random.randint(1,99999)}",
                enrollment=enrollment,
                student=user, # try using 'user' var directly
                course=course,
                gross_amount=Decimal('10.00'),
                platform_fee=Decimal('1.50'),
                instructor_revenue=Decimal('8.50'),
                payment_method='stripe'
            )
            print(f"Created: {t}")
        else:
            print("Transaction already exists for this enrollment")

    except Exception as e:
        print("CRASHED")
        print(e)
        import traceback
        traceback.print_exc()

run()
