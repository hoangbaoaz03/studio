"""
Course creation wizard - multi-step course creation
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from course.models import Course, Section, Lecture, Category


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_course_step1(request):
    """
    Step 1: Basic course information
    POST: {
        "title": "Course Title",
        "category_id": 1,
        "subcategory_id": 2  # optional
    }
    """
    if not request.user.is_instructor:
        return Response(
            {"error": "Only instructors can create courses"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    title = request.data.get('title')
    category_id = request.data.get('category_id')
    
    if not title or not category_id:
        return Response(
            {"error": "Title and category are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create draft course
    course = Course.objects.create(
        instructor=request.user,
        title=title,
        category_id=category_id,
        subcategory_id=request.data.get('subcategory_id'),
        status='draft'
    )
    
    return Response({
        "success": True,
        "course_id": course.id,
        "slug": course.slug,
        "message": "Course created. Proceed to step 2."
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_course_details(request, course_id):
    """
    Step 2: Update course details
    PATCH: {
        "subtitle": "...",
        "description": "...",
        "what_you_will_learn": ["Item 1", "Item 2"],
        "requirements": ["Req 1"],
        "target_audience": ["Audience 1"],
        "language": "English",
        "level": "beginner"
    }
    """
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Update fields
    updateable_fields = [
        'subtitle', 'description', 'what_you_will_learn',
        'requirements', 'target_audience', 'language', 'level'
    ]
    
    for field in updateable_fields:
        if field in request.data:
            setattr(course, field, request.data[field])
    
    course.save()
    
    return Response({
        "success": True,
        "message": "Course details updated. Proceed to curriculum."
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_course_section(request, course_id):
    """
    Step 3: Add curriculum sections
    POST: {
        "title": "Section Title",
        "objective": "What students will learn",
        "order": 1
    }
    """
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    title = request.data.get('title')
    if not title:
        return Response(
            {"error": "Section title is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get next order if not provided
    order = request.data.get('order')
    if order is None:
        max_order = Section.objects.filter(course=course).count()
        order = max_order + 1
    
    section = Section.objects.create(
        course=course,
        title=title,
        objective=request.data.get('objective', ''),
        order=order
    )
    
    return Response({
        "success": True,
        "section_id": section.id,
        "title": section.title
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_lecture(request, section_id):
    """
    Step 4: Add lectures to sections
    POST: {
        "title": "Lecture Title",
        "order": 1,
        "content": "Lecture description/transcript",
        "is_preview": false
    }
    """
    try:
        section = Section.objects.get(id=section_id)
        
        # Verify ownership
        if section.course.instructor != request.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
    except Section.DoesNotExist:
        return Response(
            {"error": "Section not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    title = request.data.get('title')
    if not title:
        return Response(
            {"error": "Lecture title is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get next order if not provided
    order = request.data.get('order')
    if order is None:
        max_order = Lecture.objects.filter(section=section).count()
        order = max_order + 1
    
    lecture = Lecture.objects.create(
        section=section,
        title=title,
        order=order,
        content=request.data.get('content', ''),
        is_preview=request.data.get('is_preview', False)
    )
    
    return Response({
        "success": True,
        "lecture_id": lecture.id,
        "title": lecture.title,
        "message": "Lecture created. Upload video next."
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_course_pricing(request, course_id):
    """
    Step 5: Set course pricing
    PATCH: {
        "price": "49.99",
        "discount_price": "29.99",  # optional
        "is_free": false
    }
    """
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if 'price' in request.data:
        course.price = request.data['price']
    if 'discount_price' in request.data:
        course.discount_price = request.data['discount_price']
    if 'is_free' in request.data:
        course.is_free = request.data['is_free']
    
    course.save()
    
    return Response({
        "success": True,
        "message": "Pricing updated successfully"
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_course(request, course_id):
    """
    Final step: Publish course
    """
    try:
        course = Course.objects.get(id=course_id, instructor=request.user)
    except Course.DoesNotExist:
        return Response(
            {"error": "Course not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validation
    errors = []
    
    if not course.description:
        errors.append("Course description is required")
    if not course.thumbnail:
        errors.append("Course thumbnail is required")
    if course.sections.count() == 0:
        errors.append("Course must have at least one section")
    if not course.what_you_will_learn:
        errors.append("Learning outcomes are required")
    
    # Check if sections have lectures
    for section in course.sections.all():
        if section.lectures.count() == 0:
            errors.append(f"Section '{section.title}' has no lectures")
    
    if errors:
        return Response(
            {"error": "Cannot publish course", "details": errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Publish course
    from django.utils import timezone
    course.status = 'published'
    course.published_at = timezone.now()
    course.save()
    
    # Update stats
    course.update_stats()
    
    return Response({
        "success": True,
        "message": "Course published successfully!",
        "course_url": f"/courses/{course.slug}/"
    })
