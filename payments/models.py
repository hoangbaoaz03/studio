"""
Payment models for marketplace
Transaction tracking and instructor payouts
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from course.models import Course
from result.models import Enrollment


class Transaction(models.Model):
    """
    Payment transactions for course purchases
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('free', 'Free Enrollment'),
    ]
    
    # Reference
    transaction_id = models.CharField(max_length=200, unique=True)
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='transaction'
    )
    
    # Parties
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Amounts
    gross_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text=_("Amount paid by student")
    )
    platform_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        help_text=_("Platform commission percentage")
    )
    platform_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text=_("Platform commission amount")
    )
    instructor_revenue = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text=_("Amount for instructor")
    )
    
    # Payment details
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    payment_provider_id = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Stripe charge ID, PayPal transaction ID, etc.")
    )
    
    # Coupon/discount
    coupon_code = models.CharField(max_length=50, blank=True)
    discount_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - ${self.gross_amount}"
    
    def save(self, *args, **kwargs):
        # Calculate fees
        if not self.platform_fee:
            fee_decimal = self.platform_fee_percent / Decimal('100')
            self.platform_fee = round(self.gross_amount * fee_decimal, 2)
            self.instructor_revenue = self.gross_amount - self.platform_fee
        super().save(*args, **kwargs)


class Coupon(models.Model):
    """
    Discount coupons for courses
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percent', _('Percentage')),
        ('fixed', _('Fixed Amount')),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='coupons',
        help_text=_("Leave blank for site-wide coupon")
    )
    
    # Discount
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES
    )
    discount_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Limits
    max_uses = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Maximum number of uses (blank = unlimited)")
    )
    current_uses = models.IntegerField(default=0)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_coupons'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}"
    
    def is_valid(self):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def get_discount_amount(self, price):
        """Calculate discount amount for a given price"""
        if self.discount_type == 'percent':
            return round(price * (self.discount_value / Decimal('100')), 2)
        else:  # fixed
            return min(self.discount_value, price)


class InstructorPayout(models.Model):
    """
    Monthly payouts to instructors
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
    ]
    
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts',
        limit_choices_to={'is_instructor': True}
    )
    
    # Period
    period_year = models.IntegerField()
    period_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    
    # Amounts
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Total revenue before platform fee")
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount to be paid to instructor")
    )
    
    # Payment details
    payment_method = models.CharField(max_length=50, default='bank_transfer')
    payment_reference = models.CharField(max_length=200, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-period_year', '-period_month']
        unique_together = ['instructor', 'period_year', 'period_month']
    
    def __str__(self):
        return f"{self.instructor.username} - {self.period_year}/{self.period_month:02d} (${self.payout_amount})"
