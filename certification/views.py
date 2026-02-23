from rest_framework import generics, viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Certification, CertificationProvider, UserCertificationProgress
from .serializers import (
    CertificationSerializer, 
    CertificationDetailSerializer, 
    CertificationProviderSerializer
)

class CertificationListView(generics.ListAPIView):
    queryset = Certification.objects.all().select_related('provider')
    serializer_class = CertificationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['provider__slug', 'level']
    search_fields = ['title', 'provider__name', 'description']
    ordering_fields = ['price', 'created_at']

class CertificationDetailView(generics.RetrieveAPIView):
    queryset = Certification.objects.all().select_related('provider')
    serializer_class = CertificationDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

class ProviderListView(generics.ListAPIView):
    queryset = CertificationProvider.objects.all()
    serializer_class = CertificationProviderSerializer
    permission_classes = [permissions.AllowAny]
