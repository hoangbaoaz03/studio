"""
API Views for Enrollment and Reviews
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from course.models import Course, Lecture
from core.models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Enrollment, LectureProgress, Review, Question, Answer, Wishlist
from .serializers import (
    EnrollmentSerializer,
    LectureProgressSerializer,
    ReviewSerializer,
    QuestionSerializer,
    AnswerSerializer,
    WishlistSerializer
)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for enrollments
    Students can view their enrollments and enroll in courses
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)
    
    def perform_create(self, serializer):
        """Enroll student in a course"""
        serializer.save(student=self.request.user)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get lecture progress for an enrollment"""
        enrollment = self.get_object()
        progress = LectureProgress.objects.filter(enrollment=enrollment)
        serializer = LectureProgressSerializer(progress, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_lecture_progress(self, request, pk=None):
        """Update progress for a specific lecture"""
        enrollment = self.get_object()
        lecture_id = request.data.get('lecture_id')
        last_position = request.data.get('last_position', 0)
        completed = request.data.get('completed', False)
        
        lecture = get_object_or_404(Lecture, id=lecture_id)
        
        progress, created = LectureProgress.objects.get_or_create(
            enrollment=enrollment,
            lecture=lecture
        )
        
        progress.last_position = last_position
        progress.watch_count += 1
        
        if completed and not progress.completed:
            progress.mark_complete()
        else:
            progress.save()
        
        serializer = LectureProgressSerializer(progress)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for course reviews
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        course_id = self.request.query_params.get('course', None)
        if course_id:
            return Review.objects.filter(course_id=course_id).order_by('-created_at')
        return Review.objects.filter(student=self.request.user)
    
    def perform_create(self, serializer):
        """Create a review for a course"""
        course = serializer.validated_data['course']
        
        # Check if student is enrolled
        enrollment = Enrollment.objects.filter(
            student=self.request.user,
            course=course
        ).first()
        
        if not enrollment:
            raise PermissionError("You must be enrolled to review this course")
        
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        
        try:
            review = serializer.save(student=self.request.user, enrollment=enrollment)
        except IntegrityError:
            raise ValidationError({"error": "You have already reviewed this course. Please update your existing review instead."})
        
        # Notify course instructor (primary)
        primary_instructor = course.instructor
        if primary_instructor and primary_instructor != self.request.user:
            Notification.objects.create(
                recipient=primary_instructor,
                title=f"New Review for {course.title}",
                message=f"{self.request.user.get_full_name()} wrote a review.",
                notification_type='course',
                link=f"/course/{course.slug}/learn?tab=reviews"
            )
            # Push notification via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{primary_instructor.id}",
                {"type": "send_notification", "data": {"event": "new_notification", "message": "New review received"}}
            )
        
        # Broadcast review to course channel for real-time
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"course_{course.id}",
            {
                "type": "course_event",
                "data": {
                    "event": "new_review",
                    "review": {
                        "id": review.id,
                        "student_name": self.request.user.get_full_name(),
                        "rating": review.rating,
                        "comment": review.comment,
                        "created_at": review.created_at.isoformat() if review.created_at else None,
                    }
                }
            }
        )
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark a review as helpful or not helpful"""
        review = self.get_object()
        is_helpful = request.data.get('helpful', True)
        
        from .models import ReviewHelpful
        
        # Remove previous vote if exists
        ReviewHelpful.objects.filter(
            user=request.user,
            review=review
        ).delete()
        
        # Add new vote
        ReviewHelpful.objects.create(
            user=request.user,
            review=review,
            is_helpful=is_helpful
        )
        
        # Update counts
        review.helpful_count = review.helpfulness_votes.filter(is_helpful=True).count()
        review.not_helpful_count = review.helpfulness_votes.filter(is_helpful=False).count()
        review.save()
        
        return Response({'status': 'vote recorded'})


class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Q&A questions
    """
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lecture_id = self.request.query_params.get('lecture', None)
        course_id = self.request.query_params.get('course', None)
        
        queryset = Question.objects.all()
        
        if lecture_id:
            queryset = queryset.filter(lecture_id=lecture_id)
        elif course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create a question"""
        lecture = serializer.validated_data['lecture']
        question = serializer.save(
            user=self.request.user,
            course=lecture.section.course
        )
        
        # Notify primary instructor
        course = lecture.section.course
        primary_instructor = course.instructor
        if primary_instructor and primary_instructor != self.request.user:
            Notification.objects.create(
                recipient=primary_instructor,
                title=f"New Question in {course.title}",
                message=f"{self.request.user.get_full_name()} asked: '{question.title[:50]}...'",
                notification_type='learning',
                link=f"/course/{course.slug}/learn?tab=qa&question={question.id}"
            )
            # Push notification via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{primary_instructor.id}",
                {"type": "send_notification", "data": {"event": "new_notification", "message": "New question received"}}
            )
        
        # Broadcast question to course channel for real-time
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"course_{course.id}",
            {
                "type": "course_event",
                "data": {
                    "event": "new_question",
                    "question": {
                        "id": question.id,
                        "title": question.title,
                        "question": question.question,
                        "user_name": self.request.user.get_full_name(),
                        "answers": [],
                        "answer_count": 0,
                        "created_at": question.created_at.isoformat() if question.created_at else None,
                    }
                }
            }
        )


class AnswerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Q&A answers
    """
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        question_id = self.request.query_params.get('question', None)
        if question_id:
            return Answer.objects.filter(question_id=question_id)
        return Answer.objects.all()
    
    def perform_create(self, serializer):
        """Create an answer"""
        answer = serializer.save(user=self.request.user)
        
        # Notify the question author if this is someone else answering
        question = answer.question
        if question.user != self.request.user:
            Notification.objects.create(
                recipient=question.user,
                title="New Answer to your question",
                message=f"{self.request.user.get_full_name()} answered your question: '{question.title[:50]}...'",
                notification_type='learning',
                link=f"/course/{question.course.slug}/learn?tab=qa&question={question.id}"
            )
            # Push notification via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{question.user.id}",
                {"type": "send_notification", "data": {"event": "new_notification", "message": "New answer to your question"}}
            )
        
        # Broadcast answer to course channel for real-time
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"course_{question.course.id}",
            {
                "type": "course_event",
                "data": {
                    "event": "new_answer",
                    "question_id": question.id,
                    "answer": {
                        "id": answer.id,
                        "user_name": self.request.user.get_full_name(),
                        "answer": answer.answer,
                        "is_instructor_answer": answer.is_instructor_answer,
                        "created_at": answer.created_at.isoformat() if answer.created_at else None,
                    }
                }
            }
        )
    
    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        """Upvote an answer"""
        answer = self.get_object()
        answer.upvote_count += 1
        answer.save()
        return Response({'upvote_count': answer.upvote_count})


class WishlistViewSet(viewsets.ModelViewSet):
    """
    API endpoint for wishlist
    """
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Add course to wishlist"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle course in wishlist"""
        course_id = request.data.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        wishlist_item = Wishlist.objects.filter(
            user=request.user,
            course=course
        ).first()
        
        if wishlist_item:
            wishlist_item.delete()
            return Response({'status': 'removed', 'in_wishlist': False})
        else:
            Wishlist.objects.create(user=request.user, course=course)
            return Response({'status': 'added', 'in_wishlist': True})
