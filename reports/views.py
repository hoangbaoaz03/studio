from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Report, ReportLog
from .serializers import ReportSerializer, ReportCreateSerializer
from rest_framework.permissions import IsAdminUser

class ReportViewSet(viewsets.ModelViewSet):
    """
    User: Create reports
    Admin: Manage reports
    """
    queryset = Report.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer
        
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAdminUser()]
        
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def assign(self, request, pk=None):
        report = self.get_object()
        report.assigned_to = request.user
        report.status = 'investigating'
        report.save()
        
        ReportLog.objects.create(
            report=report,
            actor=request.user,
            action='assigned',
            note='Self-assigned for investigation'
        )
        return Response(ReportSerializer(report).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        report = self.get_object()
        note = request.data.get('note', '')
        resolution = request.data.get('resolution', 'resolved') # resolved, dismissed
        
        if resolution not in ['resolved', 'dismissed']:
             return Response({'error': 'Invalid resolution status'}, status=status.HTTP_400_BAD_REQUEST)

        report.status = resolution
        report.save()
        
        ReportLog.objects.create(
            report=report,
            actor=request.user,
            action=resolution,
            note=note
        )
        return Response(ReportSerializer(report).data)
