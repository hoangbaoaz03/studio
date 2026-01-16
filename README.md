# SkyLearn Marketplace Platform

## Overview
Modern online course marketplace platform built with Django and Django REST Framework.

## Features
- 🎓 Course marketplace with categories
- 👨‍🏫 Instructor profiles and dashboards
- 📹 Video-based learning
- ⭐ Reviews and ratings
- 💬 Q&A system
- 📊 Progress tracking
- 💳 Payment integration (Stripe)
- 🔐 JWT authentication + OAuth2

## Tech Stack
- **Backend**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL (SQLite for dev)
- **Cache**: Redis
- **Task Queue**: Celery
- **Storage**: AWS S3 (for videos)
- **Payment**: Stripe

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt
```

### 2. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
```

### 3. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load sample data
python manage.py loaddata fixtures/categories.json
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit:
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## API Endpoints

### Authentication
```
POST /api/token/              # Get JWT token
POST /api/token/refresh/      # Refresh JWT token
```

### Courses
```
GET    /api/courses/courses/                # List courses
GET    /api/courses/courses/{slug}/         # Course details
POST   /api/courses/courses/                # Create course (instructor)
PATCH  /api/courses/courses/{slug}/         # Update course
GET    /api/courses/courses/featured/       # Featured courses
GET    /api/courses/courses/popular/        # Popular courses
GET    /api/courses/courses/my_courses/     # My courses (instructor)
```

### Categories
```
GET    /api/courses/categories/             # List categories
GET    /api/courses/subcategories/          # List subcategories
```

### Enrollments
```
GET    /api/learning/enrollments/           # My enrollments
POST   /api/learning/enrollments/           # Enroll in course
GET    /api/learning/enrollments/{id}/progress/  # My progress
```

### Reviews
```
GET    /api/learning/reviews/?course={id}   # Course reviews
POST   /api/learning/reviews/               # Write review
```

### Q&A
```
GET    /api/learning/questions/?lecture={id}  # Lecture questions
POST   /api/learning/questions/                # Ask question
POST   /api/learning/answers/                  # Answer question
```

### Wishlist
```
GET    /api/learning/wishlist/              # My wishlist
POST   /api/learning/wishlist/toggle/       # Add/remove course
```

## Project Structure

```
doan/
├── accounts/          # User & instructor models
├── course/            # Course, section, lecture models
├── result/            # Enrollment, review, Q&A
├── payments/          # Transaction, payout models
├── core/              # Site settings, announcements
├── config/            # Django settings & URLs
├── static/            # Static files
├── media/             # Uploaded media
└── templates/         # HTML templates
```

## Development

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Create Migrations
```bash
python manage.py makemigrations
```

## Deployment

See [deployment_guide.md](docs/deployment_guide.md) for production deployment instructions.

## License

MIT License
