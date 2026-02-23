"""
Comprehensive sample data seeder for SkyLearn
Creates Udemy-like data with multiple categories, instructors, and courses
"""
import os
import sys
import django
from decimal import Decimal
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from course.models import Category, Subcategory, Course, Section, Lecture
from accounts.models import InstructorProfile

User = get_user_model()

# Sample data
CATEGORIES_DATA = [
    {
        "name": "Python",
        "icon": "code",
        "description": "Master Python programming for data science, web development, and more",
        "subcategories": ["Python Basics", "Django", "Data Analysis", "Machine Learning"]
    },
    {
        "name": "Excel",
        "icon": "grid",
        "description": "Master Microsoft Excel for business and data analysis",
        "subcategories": ["Excel Basics", "VBA", "Data Visualization", "Pivot Tables"]
    },
    {
        "name": "Web Development",
        "icon": "globe",
        "description": "Build modern websites and applications",
        "subcategories": ["Frontend", "Backend", "Full Stack", "React", "Next.js"]
    },
    {
        "name": "JavaScript",
        "icon": "code",
        "description": "The language of the web",
        "subcategories": ["ES6+", "TypeScript", "Node.js", "Vue", "Angular"]
    },
    {
        "name": "Data Science",
        "icon": "database",
        "description": "Analyze data and build AI models",
        "subcategories": ["Statistics", "Deep Learning", "Visualization", "Big Data"]
    },
]

INSTRUCTORS_DATA = [
    {
        "username": "dr_angela",
        "email": "angela@example.com",
        "first_name": "Dr. Angela",
        "last_name": "Yu",
        "about": "I'm Angela, a developer with a passion for teaching. I've helped over 2.5 million students learn to code.",
        "total_students": 2500000,
        "total_courses": 7,
        "average_rating": Decimal("4.7")
    },
    {
        "username": "jose_portilla",
        "email": "jose@example.com",
        "first_name": "Jose",
        "last_name": "Portilla",
        "about": "Jose Portilla has BS and MS in Mechanical Engineering from Santa Clara University with years of experience in Data Science.",
        "total_students": 4000000,
        "total_courses": 32,
        "average_rating": Decimal("4.6")
    },
    {
        "username": "colt_steele",
        "email": "colt@example.com",
        "first_name": "Colt",
        "last_name": "Steele",
        "about": "Hi! I'm Colt. I'm a developer with a serious love for teaching. I've taught hundreds of bootcamp students and online.",
        "total_students": 1500000,
        "total_courses": 10,
        "average_rating": Decimal("4.8")
    },
    {
        "username": "maximilian",
        "email": "max@example.com",
        "first_name": "Maximilian",
        "last_name": "Schwarzmüller",
        "about": "As a self-taught developer, I know the hard way of learning new skills. I want to make learning more accessible.",
        "total_students": 3000000,
        "total_courses": 56,
        "average_rating": Decimal("4.6")
    },
    {
        "username": "stephen_grider",
        "email": "stephen@example.com",
        "first_name": "Stephen",
        "last_name": "Grider",
        "about": "Stephen Grider has been building complex Javascript front ends for top corporations for years.",
        "total_students": 1200000,
        "total_courses": 28,
        "average_rating": Decimal("4.7")
    },
]

COURSES_DATA = [
    # Python Courses
    {
        "instructor": "dr_angela",
        "category": "Python",
        "subcategory": "Python Basics",
        "title": "100 Days of Code: The Complete Python Pro Bootcamp",
        "subtitle": "Master Python by building 100 projects in 100 days. Learn data science, automation, build websites, games and apps!",
        "price": Decimal("84.99"),
        "discount_price": Decimal("19.99"),
        "level": "all",
        "average_rating": 4.7,
        "total_reviews": 312847,
        "total_enrollments": 1500000,
        "what_you_will_learn": [
            "You will master the Python programming language by building 100 unique projects over 100 days.",
            "You will learn automation, game, app and web development, data science and machine learning.",
            "You will be able to program in Python professionally.",
            "You will learn Selenium, Beautiful Soup, Request, Flask, Pandas, NumPy, Scikit Learn, Plotly, and Matplotlib.",
        ],
        "requirements": ["No programming experience needed"],
        "sections": [{"title": "Day 1", "lectures": ["Intro", "Setup"]}, {"title": "Day 2", "lectures": ["Variables", "Data Types"]}]
    },
    {
        "instructor": "jose_portilla",
        "category": "Python",
        "subcategory": "Data Analysis",
        "title": "Learning Python for Data Analysis and Visualization",
        "subtitle": "Learn python and how to use it to analyze,visualize and present data. Includes tons of sample code and hours of video!",
        "price": Decimal("89.99"),
        "discount_price": Decimal("13.99"),
        "level": "intermediate",
        "average_rating": 4.6,
        "total_reviews": 15400,
        "total_enrollments": 250000,
        "what_you_will_learn": ["Use Python for Data Analysis", "Use NumPy and Pandas", "Create Visualizations"],
        "requirements": ["Basic Math Skills"],
        "sections": [{"title": "Intro", "lectures": ["Welcome", "Setup"]}, {"title": "NumPy", "lectures": ["Arrays", "Indexing"]}]
    },
    {
        "instructor": "colt_steele",
        "category": "Python",
        "subcategory": "Django",
        "title": "The Ultimate Django Series: Part 1",
        "subtitle": "Master Django to build rigorous, functional and powerful web applications that are secure and scalable.",
        "price": Decimal("79.99"),
        "discount_price": Decimal("14.99"),
        "level": "advanced",
        "average_rating": 4.8,
        "total_reviews": 8900,
        "total_enrollments": 55000,
        "what_you_will_learn": ["Build Django apps", "Deploy to production", "Understand MVC"],
        "requirements": ["Python knowledge"],
        "sections": [{"title": "Getting Started", "lectures": ["Install Django", "First App"]}, {"title": "Models", "lectures": ["Creating Models", "Migrations"]}]
    },

    # Excel Courses
    {
        "instructor": "jose_portilla",
        "category": "Excel",
        "subcategory": "Excel Basics",
        "title": "Microsoft Excel - Excel from Beginner to Advanced",
        "subtitle": "Excel with this A-Z Microsoft Excel Course. Microsoft Excel 2010, 2013, 2016, Excel 2019 and Office 365",
        "price": Decimal("94.99"),
        "discount_price": Decimal("15.99"),
        "level": "all",
        "average_rating": 4.7,
        "total_reviews": 465000,
        "total_enrollments": 1800000,
        "what_you_will_learn": ["Master Excel", "Build complex formulas", "Create dashboards"],
        "requirements": ["Microsoft Excel"],
        "sections": [{"title": "Introduction", "lectures": ["Calculations", "Saving"]}, {"title": "Intermediate", "lectures": ["VLOOKUP", "Pivot Tables"]}]
    },
    {
        "instructor": "dr_angela",
        "category": "Excel",
        "subcategory": "VBA",
        "title": "Unlock Excel VBA and Excel Macros",
        "subtitle": "Automate your daily tasks and maximize your productivity with Excel VBA and Macros.",
        "price": Decimal("84.99"),
        "discount_price": Decimal("12.99"),
        "level": "intermediate",
        "average_rating": 4.5,
        "total_reviews": 32000,
        "total_enrollments": 120000,
        "what_you_will_learn": ["Automate tasks", "Write Macros", "Debug Code"],
        "requirements": ["Excel Basics"],
        "sections": [{"title": "Macros 101", "lectures": ["Recording", "Editing"]}, {"title": "VBA Syntax", "lectures": ["Variables", "Loops"]}]
    },
    {
        "instructor": "stephen_grider",
        "category": "Excel",
        "subcategory": "Data Visualization",
        "title": "Excel Data Visualization: Mastering 20+ Charts and Graphs",
        "subtitle": "Learn how to create 20+ Excel charts and graphs to tell a story with your data.",
        "price": Decimal("69.99"),
        "discount_price": Decimal("11.99"),
        "level": "intermediate",
        "average_rating": 4.6,
        "total_reviews": 11000,
        "total_enrollments": 45000,
        "what_you_will_learn": ["Create advanced charts", "Dashboard design", "Dynamic charts"],
        "requirements": ["Excel 2016+"],
        "sections": [{"title": "Column Charts", "lectures": ["Clustered", "Stacked"]}, {"title": "Line Charts", "lectures": ["Trendlines", "Formatting"]}]
    },

    # Web Development Courses
    {
        "instructor": "colt_steele",
        "category": "Web Development",
        "subcategory": "Full Stack",
        "title": "The Web Developer Bootcamp 2024",
        "subtitle": "The only course you need to learn web development - HTML, CSS, JS, Node, and More!",
        "price": Decimal("119.99"),
        "discount_price": Decimal("19.99"),
        "level": "all",
        "average_rating": 4.8,
        "total_reviews": 270000,
        "total_enrollments": 950000,
        "what_you_will_learn": ["HTML5 & CSS3", "Modern JavaScript", "Node.js & Express", "MongoDB"],
        "requirements": ["Internet access"],
        "sections": [{"title": "HTML", "lectures": ["Basics", "Forms"]}, {"title": "CSS", "lectures": ["Selectors", "Box Model"]}]
    },
    {
        "instructor": "maximilian",
        "category": "Web Development",
        "subcategory": "Frontend",
        "title": "React - The Complete Guide 2024 (incl. React Router & Redux)",
        "subtitle": "Dive in and learn React.js from scratch! Learn React, Hooks, Redux, React Router, Next.js, Best Practices and way more!",
        "price": Decimal("99.99"),
        "discount_price": Decimal("16.99"),
        "level": "intermediate",
        "average_rating": 4.7,
        "total_reviews": 210000,
        "total_enrollments": 880000,
        "what_you_will_learn": ["React Hooks", "Redux Toolkit", "Next.js"],
        "requirements": ["JavaScript Basics"],
        "sections": [{"title": "React Basics", "lectures": ["Components", "JSX"]}, {"title": "State", "lectures": ["useState", "Events"]}]
    },
    {
        "instructor": "stephen_grider",
        "category": "Web Development",
        "subcategory": "Backend",
        "title": "Microservices with Node JS and React",
        "subtitle": "Build, deploy, and scale an E-Commerce app using Microservices built with Node, React, Docker and Kubernetes",
        "price": Decimal("94.99"),
        "discount_price": Decimal("18.99"),
        "level": "advanced",
        "average_rating": 4.8,
        "total_reviews": 15000,
        "total_enrollments": 60000,
        "what_you_will_learn": ["Microservice Architecture", "Docker & Kubernetes", "Event Bus"],
        "requirements": ["Node.js", "React"],
        "sections": [{"title": "Fundamentals", "lectures": ["Monolith vs Microservices", "Data Mgmt"]}, {"title": "Mini-Microservices App", "lectures": ["Post Service", "Comment Service"]}]
    },

    # JavaScript Courses
    {
        "instructor": "maximilian",
        "category": "JavaScript",
        "subcategory": "ES6+",
        "title": "JavaScript - The Complete Guide 2024 (Beginner + Advanced)",
        "subtitle": "Modern JavaScript from the beginning - all the way up to JS expert level! the must-have JavaScript resource",
        "price": Decimal("94.99"),
        "discount_price": Decimal("15.99"),
        "level": "all",
        "average_rating": 4.7,
        "total_reviews": 85000,
        "total_enrollments": 400000,
        "what_you_will_learn": ["Modern JavaScript", "DOM Manipulation", "OOP", "Async JS"],
        "requirements": ["None"],
        "sections": [{"title": "Variables", "lectures": ["let vs const", "Types"]}, {"title": "Functions", "lectures": ["Arrow Functions", "Callbacks"]}]
    },
    {
        "instructor": "jose_portilla",
        "category": "JavaScript",
        "subcategory": "TypeScript",
        "title": "Understanding TypeScript - 2024 Edition",
        "subtitle": "Don't just learn TypeScript, understand it! The complete guide to adding types to your JavaScript code.",
        "price": Decimal("74.99"),
        "discount_price": Decimal("13.99"),
        "level": "intermediate",
        "average_rating": 4.8,
        "total_reviews": 42000,
        "total_enrollments": 180000,
        "what_you_will_learn": ["TypeScript Basics", "Interfaces & Types", "Generics", "Decorators"],
        "requirements": ["Basic JavaScript"],
        "sections": [{"title": "Getting Started", "lectures": ["Why TypeScript?", "Setup"]}, {"title": "Basics", "lectures": ["Core Types", "Objects"]}]
    },
    {
        "instructor": "dr_angela",
        "category": "JavaScript",
        "subcategory": "Node.js",
        "title": "The Complete Node.js Developer Course (3rd Edition)",
        "subtitle": "Learn Node.js by building real-world applications with Node, Express, MongoDB, Jest, and more!",
        "price": Decimal("84.99"),
        "discount_price": Decimal("14.99"),
        "level": "intermediate",
        "average_rating": 4.6,
        "total_reviews": 67000,
        "total_enrollments": 290000,
        "what_you_will_learn": ["Node.js API", "Express framework", "MongoDB", "Testing"],
        "requirements": ["JavaScript Basics"],
        "sections": [{"title": "Note App", "lectures": ["File System", "Input"]}, {"title": "Web Server", "lectures": ["Express", "Templating"]}]
    },

    # Data Science Courses
    {
        "instructor": "jose_portilla",
        "category": "Data Science",
        "subcategory": "Machine Learning",
        "title": "Python for Data Science and Machine Learning Bootcamp",
        "subtitle": "Learn how to use NumPy, Pandas, Seaborn , Matplotlib , Plotly , Scikit-Learn , Machine Learning, Tensorflow , and more!",
        "price": Decimal("109.99"),
        "discount_price": Decimal("21.99"),
        "level": "all",
        "average_rating": 4.7,
        "total_reviews": 120000,
        "total_enrollments": 600000,
        "what_you_will_learn": ["Machine Learning Algorithms", "Pandas for Data Analysis", "Data Visualization"],
        "requirements": ["Basic Python"],
        "sections": [{"title": "Intro to ML", "lectures": ["Supervised Learning", "Setup"]}, {"title": "Linear Regression", "lectures": ["Theory", "Coding"]}]
    },
    {
        "instructor": "stephen_grider",
        "category": "Data Science",
        "subcategory": "Deep Learning",
        "title": "Deep Learning with Python and Keras",
        "subtitle": "Get started with Deep Learning using the Keras library for Theano and TensorFlow.",
        "price": Decimal("89.99"),
        "discount_price": Decimal("16.99"),
        "level": "advanced",
        "average_rating": 4.5,
        "total_reviews": 18000,
        "total_enrollments": 85000,
        "what_you_will_learn": ["Neural Networks", "Keras API", "Computer Vision"],
        "requirements": ["Python", "Math"],
        "sections": [{"title": "Neural Nets", "lectures": ["Perceptrons", "Backpropagation"]}, {"title": "CNNs", "lectures": ["Convolution", "Pooling"]}]
    },
    {
        "instructor": "dr_angela",
        "category": "Data Science",
        "subcategory": "Statistics",
        "title": "Statistics for Data Science and Business Analysis",
        "subtitle": "Master the fundamentals of statistics and data analysis for data science and business intelligence.",
        "price": Decimal("64.99"),
        "discount_price": Decimal("11.99"),
        "level": "beginner",
        "average_rating": 4.6,
        "total_reviews": 45000,
        "total_enrollments": 200000,
        "what_you_will_learn": ["Descriptive Statistics", "Inferential Statistics", "Hypothesis Testing"],
        "requirements": ["None"],
        "sections": [{"title": "Basics", "lectures": ["Population vs Sample", "Types of Data"]}, {"title": "Distributions", "lectures": ["Normal Distribution", "Z-Score"]}]
    },
]


def run():
    print("🌱 Starting comprehensive database seed...")

    # 1. Create Instructors
    print("\n📚 Creating instructors...")
    instructors = {}
    for instr_data in INSTRUCTORS_DATA:
        instructor, created = User.objects.get_or_create(
            username=instr_data["username"],
            defaults={
                "email": instr_data["email"],
                "first_name": instr_data["first_name"],
                "last_name": instr_data["last_name"],
                "is_instructor": True
            }
        )
        if created:
            instructor.set_password("password123")
            instructor.save()
            print(f"  ✅ Created instructor: {instructor.get_full_name()}")
        else:
            print(f"  ⏭️ Instructor exists: {instructor.get_full_name()}")
        
        InstructorProfile.objects.update_or_create(
            user=instructor,
            defaults={
                "about": instr_data["about"],
                "total_students": instr_data["total_students"],
                "total_courses": instr_data["total_courses"],
                "average_rating": instr_data["average_rating"]
            }
        )
        instructors[instr_data["username"]] = instructor

    # 2. Create Categories
    print("\n📁 Creating categories...")
    categories = {}
    subcategories = {}
    for cat_data in CATEGORIES_DATA:
        category, created = Category.objects.get_or_create(
            name=cat_data["name"],
            defaults={"icon": cat_data["icon"], "description": cat_data["description"]}
        )
        if created:
            print(f"  ✅ Created category: {category.name}")
        categories[cat_data["name"]] = category
        
        for sub_name in cat_data["subcategories"]:
            sub, sub_created = Subcategory.objects.get_or_create(
                category=category,
                name=sub_name
            )
            subcategories[sub_name] = sub

    # 3. Create Courses
    print("\n📖 Creating courses...")
    for course_data in COURSES_DATA:
        instructor = instructors.get(course_data["instructor"])
        category = categories.get(course_data["category"])
        subcategory = subcategories.get(course_data["subcategory"])
        
        if not all([instructor, category, subcategory]):
            print(f"  ⚠️ Skipping course due to missing references: {course_data['title']}")
            continue
        
        slug = course_data["title"].lower().replace(" ", "-").replace(":", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "")[:80]
        
        course, created = Course.objects.get_or_create(
            slug=slug,
            defaults={
                "instructor": instructor,
                "title": course_data["title"],
                "subtitle": course_data["subtitle"],
                "category": category,
                "subcategory": subcategory,
                "description": f"{course_data['subtitle']}\n\nThis is a comprehensive course taught by {instructor.get_full_name()}.",
                "price": course_data["price"],
                "discount_price": course_data["discount_price"],
                "level": course_data["level"],
                "language": "English",
                "status": "published",
                "average_rating": course_data["average_rating"],
                "total_reviews": course_data["total_reviews"],
                "total_enrollments": course_data["total_enrollments"],
                "what_you_will_learn": course_data["what_you_will_learn"],
                "requirements": course_data["requirements"],
            }
        )
        
        if created:
            print(f"  ✅ Created course: {course.title}")
            
            # Create sections and lectures
            for sec_order, sec_data in enumerate(course_data["sections"], 1):
                section = Section.objects.create(
                    course=course,
                    title=sec_data["title"],
                    order=sec_order
                )
                for lec_order, lec_title in enumerate(sec_data["lectures"], 1):
                    Lecture.objects.create(
                        section=section,
                        title=lec_title,
                        order=lec_order,
                        duration=random.randint(300, 1200),
                        is_preview=(lec_order == 1)
                    )
            
            course.update_stats()
        else:
            print(f"  ⏭️ Course exists: {course.title}")

    print("\n✅ Comprehensive seeding complete!")
    print(f"   📚 {len(instructors)} instructors")
    print(f"   📁 {len(categories)} categories")
    print(f"   📖 {Course.objects.count()} courses total")


if __name__ == "__main__":
    run()
