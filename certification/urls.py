from django.urls import path
from . import views

app_name = 'certification'

urlpatterns = [
    path('certifications/', views.CertificationListView.as_view(), name='certification-list'),
    path('certifications/<slug:slug>/', views.CertificationDetailView.as_view(), name='certification-detail'),
    path('providers/', views.ProviderListView.as_view(), name='provider-list'),
]
