import os
import sys
import django
from datetime import timedelta
from django.utils import timezone
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from organization.models import Organization, Team, OrganizationMember
from course.models import Course

User = get_user_model()

def run():
    print("🏢 Seeding Organization Data...")

    # 1. Create Organization
    org_name = "Acme Corp"
    org, created = Organization.objects.get_or_create(
        name=org_name,
        defaults={
            "domain": "acme.com",
            "subscription_plan": "ENTERPRISE",
            "max_users": 100
        }
    )
    if created:
        print(f"  ✅ Created Organization: {org.name}")
    else:
        print(f"  ℹ️  Organization {org.name} already exists")

    # 2. Create Teams
    teams_data = ["Engineering", "Sales", "Marketing", "Product", "Human Resources"]
    teams = {}
    for team_name in teams_data:
        team, _ = Team.objects.get_or_create(
            organization=org,
            name=team_name
        )
        teams[team_name] = team
        print(f"  ✅ Team: {team.name}")

    # 3. Create Users and Assign to Org
    # We will create some clean users for demo
    demo_users = [
        {"username": "alice_admin", "email": "alice@acme.com", "role": "OWNER", "team": "Engineering"},
        {"username": "bob_manager", "email": "bob@acme.com", "role": "MANAGER", "team": "Sales"},
        {"username": "charlie_dev", "email": "charlie@acme.com", "role": "LEARNER", "team": "Engineering"},
        {"username": "diana_mkt", "email": "diana@acme.com", "role": "LEARNER", "team": "Marketing"},
        {"username": "evan_sales", "email": "evan@acme.com", "role": "LEARNER", "team": "Sales"},
    ]

    for user_data in demo_users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                "email": user_data['email'],
                "first_name": user_data['username'].split('_')[0].capitalize(),
                "last_name": "Demo",
                "is_active": True
            }
        )
        if created:
            user.set_password("password123")
            user.save()
            print(f"  👤 Created User: {user.username}")

        # Add to Organization
        member, m_created = OrganizationMember.objects.get_or_create(
            organization=org,
            user=user,
            defaults={
                "role": user_data['role'],
                "team": teams[user_data['team']]
            }
        )
        if m_created:
            print(f"     -> Added to {org.name} as {user_data['role']}")

    print("✅ Organization Seeding Complete!")

if __name__ == "__main__":
    run()
