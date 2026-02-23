"""
Student dashboard API
My learning, progress, certificates
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg

from result.models import Enrollment, LectureProgress, Review, Wishlist, Note
from course.models import Course, Lecture


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_learning(request):
    """
    Get all courses the student is enrolled in
    With progress and continue watching info
    """
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course', 'last_accessed_lecture').order_by('-last_accessed')
    
    my_courses = []
    for enrollment in enrollments:
        # Get next lecture to continue
        next_lecture = None
        if enrollment.last_accessed_lecture:
            # Get next lecture after last accessed
            current_section = enrollment.last_accessed_lecture.section
            next_in_section = current_section.lectures.filter(
                order__gt=enrollment.last_accessed_lecture.order
            ).first()
            
            if next_in_section:
                next_lecture = next_in_section
            else:
                # Get first lecture of next section
                next_section = enrollment.course.sections.filter(
                    order__gt=current_section.order
                ).first()
                if next_section:
                    next_lecture = next_section.lectures.first()
        else:
            # Start from beginning
            first_section = enrollment.course.sections.first()
            if first_section:
                next_lecture = first_section.lectures.first()
        
        my_courses.append({
            'enrollment_id': enrollment.id,
            'course': {
                'id': enrollment.course.id,
                'title': enrollment.course.title,
                'slug': enrollment.course.slug,
                'thumbnail': enrollment.course.thumbnail.url if enrollment.course.thumbnail else None,
                'instructor': enrollment.course.instructor.get_full_name() or enrollment.course.instructor.username,
            },
            'progress_percent': float(enrollment.progress_percent),
            'completed': enrollment.completed_at is not None,
            'enrolled_at': enrollment.enrolled_at,
            'last_accessed': enrollment.last_accessed,
            'next_lecture': {
                'id': next_lecture.id,
                'title': next_lecture.title,
                'section_title': next_lecture.section.title
            } if next_lecture else None
        })
    
    return Response({
        'total_courses': len(my_courses),
        'courses': my_courses
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_progress_stats(request):
    """
    Get overall learning statistics
    """
    enrollments = Enrollment.objects.filter(student=request.user)
    
    total_enrolled = enrollments.count()
    completed = enrollments.filter(completed_at__isnull=False).count()
    in_progress = enrollments.filter(
        progress_percent__gt=0,
        completed_at__isnull=True
    ).count()
    not_started = enrollments.filter(progress_percent=0).count()
    
    # Total learning time (estimated)
    total_minutes = 0
    for enrollment in enrollments:
        completed_lectures = LectureProgress.objects.filter(
            enrollment=enrollment,
            completed=True
        ).select_related('lecture')
        
        for progress in completed_lectures:
            total_minutes += progress.lecture.duration // 60
    
    # Reviews written
    reviews_written = Review.objects.filter(student=request.user).count()
    
    return Response({
        'total_enrolled': total_enrolled,
        'completed': completed,
        'in_progress': in_progress,
        'not_started': not_started,
        'total_learning_minutes': total_minutes,
        'reviews_written': reviews_written
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_certificates(request):
    """
    Get all earned certificates
    """
    completed_enrollments = Enrollment.objects.filter(
        student=request.user,
        completed_at__isnull=False,
        certificate_issued=True
    ).select_related('course')
    
    certificates = []
    for enrollment in completed_enrollments:
        certificates.append({
            'certificate_number': enrollment.certificate_number,
            'course_title': enrollment.course.title,
            'instructor': enrollment.course.instructor.get_full_name(),
            'completed_at': enrollment.completed_at,
            'download_url': f'/api/learning/certificate/{enrollment.id}/download/'
        })
    
    return Response({
        'total_certificates': len(certificates),
        'certificates': certificates
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_wishlist(request):
    """
    Get student's wishlist
    """
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('course')
    
    courses = []
    for item in wishlist_items:
        courses.append({
            'wishlist_id': item.id,
            'course': {
                'id': item.course.id,
                'title': item.course.title,
                'slug': item.course.slug,
                'thumbnail': item.course.thumbnail.url if item.course.thumbnail else None,
                'price': float(item.course.price),
                'discount_price': float(item.course.discount_price) if item.course.discount_price else None,
                'current_price': float(item.course.current_price),
                'instructor': item.course.instructor.get_full_name(),
                'average_rating': float(item.course.average_rating),
            },
            'added_at': item.added_at
        })
    
    return Response({
        'total_items': len(courses),
        'courses': courses
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_player_data(request, course_slug):
    """
    Get complete course data for video player page
    Includes curriculum, progress, Q&A
    """
    try:
        course = Course.objects.get(slug=course_slug, status='published')
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if student is enrolled or is instructor
    is_instructor = (course.instructor == request.user)
    enrollment = None
    
    if not is_instructor:
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course=course
            )
        except Enrollment.DoesNotExist:
            return Response(
                {"error": "You are not enrolled in this course"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Get curriculum with progress
    from course.models import Section
    sections = Section.objects.filter(course=course).prefetch_related('lectures')
    
    curriculum = []
    for section in sections:
        lectures = []
        for lecture in section.lectures.all():
            # Get progress for this lecture
            completed = False
            last_position = 0
            
            if enrollment:
                progress = LectureProgress.objects.filter(
                    enrollment=enrollment,
                    lecture=lecture
                ).first()
                if progress:
                    completed = progress.completed
                    last_position = progress.last_position
            
            lectures.append({
                'id': lecture.id,
                'title': lecture.title,
                'duration': lecture.duration,
                'video_url': lecture.video_url,
                'video_file': lecture.video_file.url if lecture.video_file else None,
                'video_source': lecture.video_source,
                'is_preview': lecture.is_preview,
                'completed': completed,
                'last_position': last_position
            })
        
        curriculum.append({
            'id': section.id,
            'title': section.title,
            'lectures': lectures
        })
    
    # Get User Notes
    notes = Note.objects.filter(
        user=request.user,
        lecture__section__course=course
    ).values('id', 'lecture_id', 'content', 'timestamp', 'created_at')

    # Get Q&A (Top 20 recent)
    from result.models import Question, Review
    questions = Question.objects.filter(course=course).select_related('user').order_by('-created_at')[:20]
    questions_data = [{
        'id': q.id,
        'title': q.title,
        'question': q.question,
        'user': q.user.username,
        'created_at': q.created_at,
        'answers_count': q.answer_count
    } for q in questions]

    # Get Reviews (Top 10 helpful)
    reviews = Review.objects.filter(course=course).select_related('student').order_by('-helpful_count', '-created_at')[:10]
    reviews_data = [{
        'id': r.id,
        'user': r.student.username,
        'rating': r.rating,
        'comment': r.comment,
        'created_at': r.created_at
    } for r in reviews]

    return Response({
        'course': {
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'instructor': course.instructor.get_full_name(),
            'what_you_will_learn': course.what_you_will_learn,
            'average_rating': course.average_rating,
            'total_reviews': course.total_reviews,
        },
        'enrollment': {
            'progress_percent': float(enrollment.progress_percent) if enrollment else 0.0,
            'last_accessed': enrollment.last_accessed if enrollment else None
        },
        'curriculum': curriculum,
        'notes': list(notes),
        'questions': questions_data,
        'reviews': reviews_data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_certificate(request, enrollment_id):
    """
    Generate certificate for completed course
    """
    try:
        enrollment = Enrollment.objects.get(
            id=enrollment_id,
            student=request.user
        )
    except Enrollment.DoesNotExist:
        return Response(
            {"error": "Enrollment not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if enrollment.completed_at is None:
        return Response(
            {"error": "Course not completed yet"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if enrollment.certificate_issued:
        return Response({
            "message": "Certificate already issued",
            "certificate_number": enrollment.certificate_number
        })
    
    # Generate certificate number
    import uuid
    enrollment.certificate_number = f"CERT-{uuid.uuid4().hex[:12].upper()}"
    enrollment.certificate_issued = True
    enrollment.save()
    
    return Response({
        "success": True,
        "certificate_number": enrollment.certificate_number,
        "download_url": f"/api/learning/certificate/{enrollment_id}/download/"
    })
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_lecture_progress(request, lecture_id):
    """
    Update progress for a specific lecture
    """
    try:
        lecture = Lecture.objects.get(id=lecture_id)
        # Find enrollment
        enrollment = Enrollment.objects.get(
            student=request.user,
            course=lecture.section.course
        )
    except (Lecture.DoesNotExist, Enrollment.DoesNotExist):
        return Response({"error": "Invalid lecture or not enrolled"}, status=400)
    
    completed = request.data.get('completed', False)
    
    progress, created = LectureProgress.objects.get_or_create(
        enrollment=enrollment,
        lecture=lecture
    )
    
    if completed and not progress.completed:
        progress.mark_complete()
    
    progress.save()
    
    # Update last accessed
    enrollment.last_accessed_lecture = lecture
    enrollment.save()
    
    return Response({"success": True, "progress": enrollment.progress_percent})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notes(request, course_slug):
    """
    Get all notes for a course
    """
    try:
        course = Course.objects.get(slug=course_slug)
        # Verify enrollment
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
             return Response({"error": "Not enrolled"}, status=403)
             
        notes = Note.objects.filter(
            user=request.user,
            lecture__section__course=course
        ).select_related('lecture')
        
        data = []
        for note in notes:
            data.append({
                'id': note.id,
                'lecture_id': note.lecture.id,
                'lecture_title': note.lecture.title,
                'content': note.content,
                'timestamp': note.timestamp,
                'created_at': note.created_at
            })
            
        return Response(data)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_note(request):
    """
    Create or update a note
    """
    lecture_id = request.data.get('lecture_id')
    content = request.data.get('content')
    timestamp = request.data.get('timestamp', 0)
    note_id = request.data.get('id')
    
    if not all([lecture_id, content]):
        return Response({"error": "Missing required fields"}, status=400)
        
    try:
        if note_id:
            note = Note.objects.get(id=note_id, user=request.user)
            note.content = content
            note.save()
        else:
            note = Note.objects.create(
                user=request.user,
                lecture_id=lecture_id,
                content=content,
                timestamp=timestamp
            )
            
        return Response({
            'id': note.id,
            'content': note.content,
            'timestamp': note.timestamp
        })
    except Exception as e:
        return Response({"error": str(e)}, status=400)
