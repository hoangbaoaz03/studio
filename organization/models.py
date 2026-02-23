from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    PLAN_CHOICES = (
        ('BASIC', 'Basic (Up to 5 users)'),
        ('PRO', 'Pro (Up to 50 users)'),
        ('ENTERPRISE', 'Enterprise (Unlimited)'),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    domain = models.CharField(max_length=255, blank=True, null=True, help_text="Auto-join domain (e.g. google.com)")
    
    # Billing / Subscription
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='BASIC')
    max_users = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    
    logo = models.ImageField(upload_to='organizations/logos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class BusinessLead(models.Model):
    """
    Capture inquiries from the /business/contact page
    """
    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('CONVERTED', 'Converted'),
        ('CLOSED', 'Closed'),
    )

    TYPE_CHOICES = (
        ('CONTACT', 'General Inquiry'),
        ('DEMO', 'Demo Request'),
    )

    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='CONTACT')

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    company_name = models.CharField(max_length=255)
    team_size = models.CharField(max_length=50) # Dropdown: 1-10, 11-50, etc
    message = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.full_name}"

class Team(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class OrganizationMember(models.Model):
    ROLE_CHOICES = (
        ('OWNER', 'Owner'),
        ('ADMIN', 'Administrator'),
        ('MANAGER', 'Manager'),
        ('LEARNER', 'Learner'),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization_memberships')
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LEARNER')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
