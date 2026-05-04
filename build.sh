#!/usr/bin/env bash
# Build script for Render
set -o errexit

pip install -r requirements.txt
pip install gunicorn dj-database-url

python manage.py collectstatic --no-input
python manage.py migrate
