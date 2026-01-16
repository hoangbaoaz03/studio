"""
URL routing for homepage and discovery
"""
from django.urls import path
from . import homepage_api, recommendations

app_name = 'core'

urlpatterns = [
    path('homepage/', homepage_api.homepage_data, name='homepage'),
    path('search/', homepage_api.search_courses, name='search'),
    path('category/<slug:slug>/', homepage_api.category_courses, name='category-courses'),
    path('instructor/<int:instructor_id>/', homepage_api.instructor_profile, name='instructor-profile'),
    path('trending/', homepage_api.trending_courses, name='trending'),
    
    # Recommendations
    path('recommendations/for-you/', recommendations.recommended_for_you, name='recommended-for-you'),
    path('recommendations/similar/<int:course_id>/', recommendations.similar_courses, name='similar-courses'),
    path('recommendations/also-bought/<int:course_id>/', recommendations.students_also_bought, name='also-bought'),
    path('recommendations/top-rated/<int:category_id>/', recommendations.top_rated_in_category, name='top-rated-category'),
    path('recommendations/because-viewed/<int:course_id>/', recommendations.because_you_viewed, name='because-viewed'),
    path('recommendations/homepage/', recommendations.personalized_homepage, name='personalized-homepage'),
]
