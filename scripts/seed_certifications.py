import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from certification.models import CertificationProvider, Certification, ExamModule, PracticeExam, Question
from django.utils.text import slugify

def run():
    print("🌱 Seeding Certification Data...")

    # 1. Providers
    providers_data = [
        {"name": "Amazon Web Services", "slug": "aws", "description": "Cloud computing certifications"},
        {"name": "Project Management Institute", "slug": "pmi", "description": "Global project management standards"},
        {"name": "Cisco", "slug": "cisco", "description": "Networking and security certifications"},
        {"name": "Microsoft", "slug": "microsoft", "description": "Azure and software development"},
        {"name": "Google Cloud", "slug": "google-cloud", "description": "GCP Cloud certifications"},
    ]
    
    providers = {}
    for p_data in providers_data:
        provider, created = CertificationProvider.objects.get_or_create(
            slug=p_data['slug'],
            defaults={'name': p_data['name'], 'description': p_data['description']}
        )
        providers[p_data['slug']] = provider
        if created: print(f"  ✅ Provider: {p_data['name']}")

    # 2. Certifications
    # Using placeholder images from ui-avatars or similar for demo purposes, 
    # since we don't have local assets.
    # In production, these would be real S3 URLs.
    
    certs_data = [
        {
            "provider": "aws",
            "title": "AWS Certified Solutions Architect - Associate",
            "level": "Associate",
            "price": 149.99,
            "prep_time": "3-6 months",
            "description": "Comprehensive preparation for the SAA-C03 exam. Covers all domains including Resilient Architecture, High Performance, and Cost Optimization.",
            "syllabus": ["IAM & Security", "EC2 & Compute", "S3 & Storage", "VPC & Networking", "Databases (RDS, DynamoDB)", "Serverless (Lambda)"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/1024px-Amazon_Web_Services_Logo.svg.png"
        },
        {
            "provider": "pmi",
            "title": "Project Management Professional (PMP)",
            "level": "Professional",
            "price": 199.99,
            "prep_time": "4-8 months",
            "description": "The gold standard in project management. Aligned with the PMBOK Guide 7th Edition.",
            "syllabus": ["People Domain", "Process Domain", "Business Environment", "Agile & Hybrid Approaches"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Pmi-logo.svg/1200px-Pmi-logo.svg.png"
        },
        {
            "provider": "cisco",
            "title": "Cisco Certified Network Associate (CCNA)",
            "level": "Associate",
            "price": 129.99,
            "prep_time": "3-5 months",
            "description": "Master the fundamentals of networking, IP connectivity, security fundamentals, and automation.",
            "syllabus": ["Network Fundamentals", "Network Access", "IP Connectivity", "IP Services", "Security Fundamentals", "Automation"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Cisco_logo_blue_2016.svg/1200px-Cisco_logo_blue_2016.svg.png"
        },
        {
            "provider": "microsoft",
            "title": "Azure Fundamentals (AZ-900)",
            "level": "Beginner",
            "price": 49.99,
            "prep_time": "2-4 weeks",
            "description": "Foundational knowledge of cloud services and how those services are provided with Microsoft Azure.",
            "syllabus": ["Cloud Concepts", "Azure Architecture", "Compute & Networking", "Storage & Databases"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Microsoft_Azure.svg/1024px-Microsoft_Azure.svg.png"
        },
        # NEW CERTIFICATIONS
        {
            "provider": "google-cloud",
            "title": "Google Professional Data Engineer",
            "level": "Professional",
            "price": 199.99,
            "prep_time": "3-5 months",
            "description": "Demonstrate proficiency in designing and building data processing systems on Google Cloud Platform.",
            "syllabus": ["Data Processing Systems", "Machine Learning Models", "Data Pipelines", "Security & Compliance"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Google_Cloud_logo.svg/1024px-Google_Cloud_logo.svg.png"
        },
        {
            "provider": "aws",
            "title": "AWS Certified Developer - Associate",
            "level": "Associate",
            "price": 149.99,
            "prep_time": "3-6 months",
            "description": "Validate your proficiency in developing, deploying, and debugging cloud-based applications using AWS.",
            "syllabus": ["Deployment", "Security", "Development with AWS Services", "Refactoring", "Monitoring and Troubleshooting"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/1024px-Amazon_Web_Services_Logo.svg.png"
        },
        {
            "provider": "pmi",
            "title": "Certified Associate in Project Management (CAPM)",
            "level": "Associate",
            "price": 129.99,
            "prep_time": "2-3 months",
            "description": "An entry-level certification for project practitioners. Designed for those with less project experience.",
            "syllabus": ["Project Environment", "Role of Project Manager", "Project Integration Management", "Project Scope Management"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Pmi-logo.svg/1200px-Pmi-logo.svg.png"
        },
        {
            "provider": "cisco",
            "title": "Cisco Certified CyberOps Associate",
            "level": "Associate",
            "price": 129.99,
            "prep_time": "3-4 months",
            "description": "Prepare for a career in cybersecurity operations. Covers security concepts, monitoring, and analysis.",
            "syllabus": ["Security Concepts", "Security Monitoring", "Host-Based Analysis", "Network Intrusion Analysis", "Security Policies"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Cisco_logo_blue_2016.svg/1200px-Cisco_logo_blue_2016.svg.png"
        },
        {
            "provider": "microsoft",
            "title": "Microsoft Power BI Data Analyst Associate (PL-300)",
            "level": "Associate",
            "price": 165.00,
            "prep_time": "2-4 months",
            "description": "Demonstrate methods and best practices for modeling, visualizing, and analyzing data with Power BI.",
            "syllabus": ["Prepare the Data", "Model the Data", "Visualize and Analyze the Data", "Deploy and Maintain Assets"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/New_Power_BI_Logo.svg/1024px-New_Power_BI_Logo.svg.png"
        },
        {
            "provider": "google-cloud",
            "title": "Google Associate Cloud Engineer",
            "level": "Associate",
            "price": 125.00,
            "prep_time": "2-4 months",
            "description": "Deploy applications, monitor operations, and manage enterprise solutions on Google Cloud.",
            "syllabus": ["Setting up a Cloud Solution Environment", "Planning and Configuring a Cloud Solution", "Deploying and Implementing a Cloud Solution", "Ensuring Successful Operation of a Cloud Solution"],
            "badge": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Google_Cloud_logo.svg/1024px-Google_Cloud_logo.svg.png"
        }
    ]

    for c_data in certs_data:
        slug = slugify(c_data['title'])
        cert, created = Certification.objects.get_or_create(
            slug=slug,
            defaults={
                "provider": providers[c_data['provider']],
                "title": c_data['title'],
                "level": c_data['level'],
                "price": Decimal(str(c_data['price'])),
                "estimated_prep_time": c_data['prep_time'],
                "description": c_data['description'],
                "syllabus": c_data['syllabus'],
                "badge_image_url": c_data['badge']
            }
        )
        
        # In case the cert already exists (from previous run), update the badge
        if not created and not cert.badge_image_url:
            cert.badge_image_url = c_data['badge']
            cert.save()
            print(f"  updated badge for: {cert.title}")
        
        if created:
            print(f"  ✅ Certification: {cert.title}")
            
            # Add Modules
            for i, topic in enumerate(c_data['syllabus'], 1):
                ExamModule.objects.create(
                    certification=cert,
                    title=f"Module {i}: {topic}",
                    order=i,
                    content=f"## {topic}\n\nKey concepts covered in this module...",
                    duration_minutes=60
                )
            
            # Add Practice Exam
            exam = PracticeExam.objects.create(
                certification=cert,
                title=f"{c_data['title']} - Full Mock Exam 1",
                duration_minutes=90,
                total_questions=60
            )
            
            # Add Questions
            for q_i in range(1, 6):
                Question.objects.create(
                    exam=exam,
                    text=f"Sample Question {q_i} for {c_data['title']}?",
                    explanation="This is the specific reason why Option A is correct...",
                    answers=[
                        {"id": 1, "text": "Correct Option", "is_correct": True},
                        {"id": 2, "text": "Distractor 1", "is_correct": False},
                        {"id": 3, "text": "Distractor 2", "is_correct": False},
                        {"id": 4, "text": "Distractor 3", "is_correct": False},
                    ]
                )

    print("✅ Seeding Complete!")

if __name__ == "__main__":
    run()
