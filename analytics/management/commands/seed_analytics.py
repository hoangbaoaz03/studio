from django.core.management.base import BaseCommand
from django.utils import timezone
from analytics.models import DailyMetric
from payments.models import Transaction, Order
from course.models import Course, Category
from accounts.models import User
import random
from datetime import timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seeds sample analytics data for the last 30 days'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding analytics data...")
        
        # Ensure we have some courses and users
        courses = list(Course.objects.filter(status='published'))
        if not courses:
            self.stdout.write(self.style.WARNING("No published courses found. Using placeholders? No, skipping transaction generation if no courses."))
        
        # 1. Generate Daily Metrics (Trend Data)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        current_date = start_date
        total_users_base = 100
        
        while current_date <= end_date:
            # Randomize daily stats
            new_users = random.randint(5, 20)
            total_users_base += new_users
            
            daily_revenue = random.randint(200, 1000)
            platform_revenue = daily_revenue * 0.15
            
            DailyMetric.objects.update_or_create(
                date=current_date,
                defaults={
                    'new_users': new_users,
                    'active_users': random.randint(50, total_users_base),
                    'total_users': total_users_base,
                    'total_revenue': Decimal(daily_revenue),
                    'platform_revenue': Decimal(platform_revenue),
                    'new_courses': random.randint(0, 3),
                    'total_enrollments': random.randint(10, 50),
                }
            )
            current_date += timedelta(days=1)
            
        self.stdout.write(self.style.SUCCESS("Daily Metrics seeded."))

        # 2. Generate Transactions (For Top Courses & Categories)
        # We need these for the 'Top Courses' table which queries real Transactions
        if courses:
            # Create a dummy student if needed
            student, _ = User.objects.get_or_create(username='analytics_test_user', defaults={'email': 'test@example.com'})
            
            # Create transactions distributed over the last 30 days
            for _ in range(50): # 50 random transactions
                course = random.choice(courses)
                tx_date = end_date - timedelta(days=random.randint(0, 30))
                price = course.price if course.price > 0 else Decimal('19.99')
                
                # We need to manually set created_at, doing it via update() after create 
                # or simpler: create object then update created_at
                
                # Mock transaction
                try:
                    # Need a fake enrollment for the OneToOne field? 
                    # Actually Transaction has OneToOne to Enrollment.
                    # Creating full Enrollment chain is complex.
                    # For Analytics/TopCourses, we query Transaction directly.
                    # Let's see if we can get away with just Transaction if we skip foreign key constraints? 
                    # No, Django enforces FK.
                    
                    # Alternative: We just mock the CourseMetric if we used that. 
                    # But my view queries Transaction.
                    
                    # OK, let's create simplified Order/Transaction if possible, 
                    # OR just accept that 'Top Courses' might be empty unless we have real enrollments.
                    
                    # Wait, 'Transaction' model requires 'enrollment'.
                    from result.models import Enrollment
                    
                    enrollment = Enrollment.objects.create(
                        student=student,
                        course=course,
                        # enrolled_at is auto_now_add, we'll patch it later if needed
                    )
                    
                    tx = Transaction.objects.create(
                        transaction_id=f"seed-{random.randint(100000, 999999)}",
                        enrollment=enrollment,
                        student=student,
                        course=course,
                        gross_amount=price,
                        platform_fee=price * Decimal('0.15'),
                        instructor_revenue=price * Decimal('0.85'),
                        payment_method='stripe',
                        status='completed',
                    )
                    
                    # Hack to set past date
                    tx.created_at = timezone.make_aware(timezone.datetime.combine(tx_date, timezone.datetime.min.time()))
                    tx.save()
                    
                except Exception as e:
                    # Avoid crashing on unique constraints if re-running
                    continue

            self.stdout.write(self.style.SUCCESS("Sample Transactions seeded."))
        else:
             self.stdout.write(self.style.WARNING("Skipping Transactions: No courses available."))

        self.stdout.write(self.style.SUCCESS("Analytics seeding completed!"))
