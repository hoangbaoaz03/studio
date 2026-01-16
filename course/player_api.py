"""
Video player helper utilities
Provides video streaming URLs, progress tracking, and playback utilities
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from course.models import Lecture
from result.models import Enrollment, LectureProgress


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_stream_url(request, lecture_id):
    """
    Get video streaming URL for a lecture
    Checks enrollment before providing access
    """
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.section.course
    
    # Check if free preview
    if lecture.is_preview:
        return Response({
            'video_url': lecture.video_url,
            'duration': lecture.duration,
            'is_preview': True
        })
    
    # Check enrollment
    try:
        enrollment = Enrollment.objects.get(
            student=request.user,
            course=course
        )
    except Enrollment.DoesNotExist:
        return Response(
            {"error": "You must enroll to watch this video"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create progress record
    progress, created = LectureProgress.objects.get_or_create(
        enrollment=enrollment,
        lecture=lecture
    )
    
    return Response({
        'video_url': lecture.video_url,
        'duration': lecture.duration,
        'last_position': progress.last_position,
        'completed': progress.completed,
        'is_preview': False
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_playback_progress(request, lecture_id):
    """
    Update video playback progress
    POST: {
        "current_position": 123,  # seconds
        "completed": false
    }
    """
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.section.course
    
    # Get enrollment
    try:
        enrollment = Enrollment.objects.get(
            student=request.user,
            course=course
        )
    except Enrollment.DoesNotExist:
        return Response(
            {"error": "Not enrolled"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Update progress
    progress, created = LectureProgress.objects.get_or_create(
        enrollment=enrollment,
        lecture=lecture
    )
    
    current_position = request.data.get('current_position', 0)
    completed = request.data.get('completed', False)
    
    progress.last_position = current_position
    progress.watch_count = progress.watch_count + 1 if created else progress.watch_count + 1
    
    # Mark as complete if watched 90% or explicitly marked
    if completed or (current_position >= lecture.duration * 0.9):
        if not progress.completed:
            progress.mark_complete()
    else:
        progress.save()
    
    # Update enrollment's last accessed lecture
    enrollment.last_accessed_lecture = lecture
    enrollment.save()
    
    return Response({
        'success': True,
        'progress_percent': float(enrollment.progress_percent)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_lecture(request, lecture_id):
    """
    Get the next lecture in the course
    """
    current_lecture = get_object_or_404(Lecture, id=lecture_id)
    current_section = current_lecture.section
    course = current_section.course
    
    # Try to get next lecture in same section
    next_lecture = current_section.lectures.filter(
        order__gt=current_lecture.order
    ).first()
    
    if next_lecture:
        return Response({
            'id': next_lecture.id,
            'title': next_lecture.title,
            'section_title': current_section.title,
            'duration': next_lecture.duration
        })
    
    # Get first lecture of next section
    next_section = course.sections.filter(
        order__gt=current_section.order
    ).first()
    
    if next_section:
        next_lecture = next_section.lectures.first()
        if next_lecture:
            return Response({
                'id': next_lecture.id,
                'title': next_lecture.title,
                'section_title': next_section.title,
                'duration': next_lecture.duration
            })
    
    # No more lectures
    return Response({
        'message': 'Course completed',
        'completed': True
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_lecture_resources(request, lecture_id):
    """
    Get downloadable resources for a lecture
    """
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.section.course
    
    # Check enrollment (or preview)
    if not lecture.is_preview:
        try:
            Enrollment.objects.get(
                student=request.user,
                course=course
            )
        except Enrollment.DoesNotExist:
            return Response(
                {"error": "Not enrolled"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    return Response({
        'lecture_title': lecture.title,
        'resources': lecture.resources,
        'content': lecture.content
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_subtitles(request, lecture_id):
    """
    Get video subtitles/captions if available
    Placeholder for future implementation
    """
    lecture = get_object_or_404(Lecture, id=lecture_id)
    
    # TODO: Implement subtitle storage and retrieval
    # For now, return empty
    return Response({
        'subtitles': [],
        'available_languages': []
    })
