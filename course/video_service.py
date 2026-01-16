"""
Video upload and processing service
Handles video upload to S3, generates thumbnails, and processes videos
"""
import os
import uuid
import boto3
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from course.models import Lecture


class VideoUploadService:
    """
    Service for handling video uploads to AWS S3
    """
    
    def __init__(self):
        if settings.USE_S3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        else:
            self.s3_client = None
            self.bucket_name = None
    
    def generate_presigned_upload_url(self, filename, content_type='video/mp4'):
        """
        Generate a presigned URL for direct upload from browser to S3
        This allows large video files to be uploaded directly without going through Django
        """
        if not self.s3_client:
            return None
        
        # Generate unique filename
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"videos/{uuid.uuid4()}{file_extension}"
        
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': unique_filename,
                    'ContentType': content_type,
                },
                ExpiresIn=3600  # URL expires in 1 hour
            )
            
            return {
                'upload_url': presigned_url,
                's3_key': unique_filename,
                'cloudfront_url': f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{unique_filename}"
            }
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def get_video_url(self, s3_key):
        """
        Get CloudFront URL for a video
        """
        if settings.USE_S3:
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
        return None
    
    def delete_video(self, s3_key):
        """
        Delete video from S3
        """
        if not self.s3_client:
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except Exception as e:
            print(f"Error deleting video: {e}")
            return False


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_upload_url(request):
    """
    Generate presigned URL for video upload
    POST: { "filename": "video.mp4", "content_type": "video/mp4" }
    """
    if not request.user.is_instructor:
        return Response(
            {"error": "Only instructors can upload videos"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    filename = request.data.get('filename')
    content_type = request.data.get('content_type', 'video/mp4')
    
    if not filename:
        return Response(
            {"error": "Filename is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    video_service = VideoUploadService()
    upload_data = video_service.generate_presigned_upload_url(filename, content_type)
    
    if not upload_data:
        return Response(
            {"error": "Could not generate upload URL. Check S3 configuration."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response(upload_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def attach_video_to_lecture(request):
    """
    Attach uploaded video to a lecture
    POST: {
        "lecture_id": 123,
        "s3_key": "videos/uuid.mp4",
        "duration": 1234  # in seconds
    }
    """
    if not request.user.is_instructor:
        return Response(
            {"error": "Permission denied"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    lecture_id = request.data.get('lecture_id')
    s3_key = request.data.get('s3_key')
    duration = request.data.get('duration', 0)
    
    try:
        lecture = Lecture.objects.get(id=lecture_id)
        
        # Verify instructor owns this course
        if lecture.section.course.instructor != request.user:
            return Response(
                {"error": "You don't own this course"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update lecture with video info
        video_service = VideoUploadService()
        lecture.video_url = video_service.get_video_url(s3_key)
        lecture.duration = duration
        lecture.save()
        
        # Update course total duration
        lecture.section.course.update_stats()
        
        return Response({
            "success": True,
            "lecture_id": lecture.id,
            "video_url": lecture.video_url
        })
        
    except Lecture.DoesNotExist:
        return Response(
            {"error": "Lecture not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def upload_video_local(request):
    """
    Upload video to local media folder (for development without S3)
    """
    if not request.user.is_instructor:
        return Response(
            {"error": "Only instructors can upload videos"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    video_file = request.FILES.get('video')
    if not video_file:
        return Response(
            {"error": "No video file provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Save to media folder
    from django.core.files.storage import default_storage
    
    filename = f"videos/{uuid.uuid4()}_{video_file.name}"
    filepath = default_storage.save(filename, video_file)
    video_url = default_storage.url(filepath)
    
    return Response({
        "success": True,
        "video_url": video_url,
        "filepath": filepath
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_video(request, lecture_id):
    """
    Delete video from lecture and S3
    """
    try:
        lecture = Lecture.objects.get(id=lecture_id)
        
        # Verify instructor owns this course
        if lecture.section.course.instructor != request.user:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete from S3 if applicable
        # TODO: Extract S3 key from video_url and delete
        
        # Remove video from lecture
        lecture.video_url = ''
        lecture.duration = 0
        lecture.save()
        
        # Update course stats
        lecture.section.course.update_stats()
        
        return Response({"success": True})
        
    except Lecture.DoesNotExist:
        return Response(
            {"error": "Lecture not found"},
            status=status.HTTP_404_NOT_FOUND
        )
