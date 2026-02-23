# Backend Utility Scripts

This directory contains maintenance and data seeding scripts for the Backend.

## Data Seeding & Content
- **`seed_udemy_data.py`**: The main seeding script. Creates Instructors, Categories, and a base set of Udemy-like Courses.
- **`bulk_add_courses.py`**: Generates a large volume of courses to populate the platform for load testing and demo purposes.
- **`add_more_courses.py`**: Adds specific additional courses to ensure all categories have content.
- **`populate_missing_courses.py`**: Checks for empty categories and fills them.
- **`enrich_courses.py`**: Adds more detailed metadata (sections, lectures) to existing courses.

## Maintenance
- **`update_thumbnails.py`**: Updates course thumbnails, likely fetching from external sources or setting placeholders.
- **`translate_data.py`**: Handles translation of course content (if using `modeltranslation`).
- **`migrate_categories_to_tree.py`**: Migrates flat category structures to MPTT (tree) structure.
- **`verify_auth.py`**: Utility to verify authentication tokens or user states.

## Usage
Run these seeds via `python manage.py shell` or directly if they setup django:
```bash
cd doan
python scripts/seed_udemy_data.py
```
