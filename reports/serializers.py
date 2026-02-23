from rest_framework import serializers
from .models import Report, ReportLog
from django.contrib.contenttypes.models import ContentType

class ReportLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.full_name', read_only=True)
    
    class Meta:
        model = ReportLog
        fields = ['id', 'actor', 'actor_name', 'action', 'note', 'created_at']

class ReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source='reporter.full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    logs = ReportLogSerializer(many=True, read_only=True)
    
    # Content fields
    content_type_str = serializers.CharField(source='content_type.model', read_only=True)
    content_object_str = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reporter_name',
            'content_type', 'object_id', 'content_type_str', 'content_object_str',
            'reason', 'description', 
            'status', 'assigned_to', 'assigned_to_name',
            'created_at', 'updated_at',
            'logs'
        ]
        read_only_fields = ['status', 'assigned_to', 'reporter']

    def get_content_object_str(self, obj):
        return str(obj.content_object)

class ReportCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating reports
    """
    content_type = serializers.CharField() # e.g. 'course', 'review'

    class Meta:
        model = Report
        fields = ['content_type', 'object_id', 'reason', 'description']
        
    def validate_content_type(self, value):
        from course.models import Course, Review
        # Simple mapping for now
        mapping = {
            'course': ContentType.objects.get_for_model(Course),
            # 'review': ContentType.objects.get_for_model(Review), # If review exists
            # Add other models as needed
        }
        
        if value not in mapping:
             # Try to find by model string
             try:
                 return ContentType.objects.get(model=value)
             except ContentType.DoesNotExist:
                 raise serializers.ValidationError("Invalid content type")
        
        return mapping[value]
