from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doan.accounts.models import InstructorProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a test instructor account'

    def handle(self, *args, **options):
        username = 'instructor'
        email = 'instructor@example.com'
        password = 'password123'
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists."))
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"User '{username}' created."))

        # Update attributes
        user.first_name = "Test"
        user.last_name = "Instructor"
        user.is_instructor = True
        user.save()
        
        # Ensure profile exists
        if not hasattr(user, 'instructor_profile'):
            InstructorProfile.objects.create(user=user, about="I am a test instructor.")
            self.stdout.write(self.style.SUCCESS("Instructor profile created."))
        else:
             self.stdout.write(self.style.WARNING("Instructor profile already exists."))
            
        self.stdout.write(self.style.SUCCESS(f"\nLogin Details:\nUsername: {username}\nPassword: {password}"))
