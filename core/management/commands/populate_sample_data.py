"""
Management command to populate database with sample data
Usage: python manage.py populate_sample_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from course.models import Category, Subcategory, Course, Section, Lecture
from accounts.models import InstructorProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create categories
        categories_data = [
            {'name': 'Development', 'slug': 'development', 'icon': 'fas fa-code'},
            {'name': 'Business', 'slug': 'business', 'icon': 'fas fa-briefcase'},
            {'name': 'Design', 'slug': 'design', 'icon': 'fas fa-palette'},
            {'name': 'Marketing', 'slug': 'marketing', 'icon': 'fas fa-bullhorn'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'  Created category: {category.name}')

        # Create subcategories
        dev_category = Category.objects.get(slug='development')
        subcats = [
            {'name': 'Web Development', 'slug': 'web-development'},
            {'name': 'Mobile Development', 'slug': 'mobile-development'},
            {'name': 'Data Science', 'slug': 'data-science'},
        ]
        
        for subcat_data in subcats:
            subcat, created = Subcategory.objects.get_or_create(
                category=dev_category,
                slug=subcat_data['slug'],
                defaults=subcat_data
            )
            if created:
                self.stdout.write(f'  Created subcategory: {subcat.name}')

        # Create sample instructors
        instructor1, created = User.objects.get_or_create(
            username='john_instructor',
            defaults={
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_instructor': True
            }
        )
        if created:
            instructor1.set_password('password123')
            instructor1.save()
            InstructorProfile.objects.create(
                user=instructor1,
                about='Experienced web developer with 10+ years'
            )
            self.stdout.write(f'  Created instructor: {instructor1.username}')

        instructor2, created = User.objects.get_or_create(
            username='jane_instructor',
            defaults={
                'email': 'jane@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'is_instructor': True
            }
        )
        if created:
            instructor2.set_password('password123')
            instructor2.save()
            InstructorProfile.objects.create(
                user=instructor2,
                about='Python expert and data scientist'
            )
            self.stdout.write(f'  Created instructor: {instructor2.username}')

        # Create sample courses
        web_dev = Subcategory.objects.get(slug='web-development')
        
        course1, created = Course.objects.get_or_create(
            slug='complete-web-development',
            defaults={
                'title': 'Complete Web Development Bootcamp',
                'subtitle': 'Learn HTML, CSS, JavaScript, and React',
                'instructor': instructor1,
                'category': dev_category,
                'subcategory': web_dev,
                'description': 'Master web development from scratch',
                'what_you_will_learn': ['HTML5 & CSS3', 'JavaScript ES6+', 'React fundamentals'],
                'requirements': ['Basic computer skills'],
                'target_audience': ['Beginners', 'Career switchers'],
                'price': 49.99,
                'discount_price': 29.99,
                'language': 'English',
                'level': 'beginner',
                'status': 'published'
            }
        )
        if created:
            self.stdout.write(f'  Created course: {course1.title}')
            
            # Add sections and lectures
            section1 = Section.objects.create(
                course=course1,
                title='Introduction to HTML',
                order=1
            )
            Lecture.objects.create(
                section=section1,
                title='What is HTML?',
                order=1,
                duration=600,
                is_preview=True
            )
            Lecture.objects.create(
                section=section1,
                title='HTML Elements and Tags',
                order=2,
                duration=900
            )

        course2, created = Course.objects.get_or_create(
            slug='python-for-data-science',
            defaults={
                'title': 'Python for Data Science',
                'subtitle': 'Master Python, NumPy, Pandas, and Matplotlib',
                'instructor': instructor2,
                'category': dev_category,
                'subcategory': Subcategory.objects.get(slug='data-science'),
                'description': 'Learn Python for data analysis and visualization',
                'what_you_will_learn': ['Python basics', 'NumPy', 'Pandas', 'Data visualization'],
                'requirements': ['No programming experience needed'],
                'target_audience': ['Aspiring data scientists'],
                'price': 79.99,
                'language': 'English',
                'level': 'intermediate',
                'status': 'published'
            }
        )
        if created:
            self.stdout.write(f'  Created course: {course2.title}')

        # Create sample student
        student, created = User.objects.get_or_create(
            username='student_user',
            defaults={
                'email': 'student@example.com',
                'first_name': 'Alice',
                'last_name': 'Student'
            }
        )
        if created:
            student.set_password('password123')
            student.save()
            self.stdout.write(f'  Created student: {student.username}')

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write('Login credentials:')
        self.stdout.write('  Instructor 1: john_instructor / password123')
        self.stdout.write('  Instructor 2: jane_instructor / password123')
        self.stdout.write('  Student: student_user / password123')
