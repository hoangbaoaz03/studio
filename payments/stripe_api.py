"""
Stripe payment integration
Handles checkout, webhooks, and enrollment creation
"""
import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from course.models import Course
from result.models import Enrollment
from payments.models import Transaction, Coupon

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Create Stripe checkout session for course purchase
    POST: {
        "course_id": 123,
        "coupon_code": "SUMMER50"  # optional
    }
    """
    course_id = request.data.get('course_id')
    coupon_code = request.data.get('coupon_code')
    
    course = get_object_or_404(Course, id=course_id, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return Response(
            {"error": "You are already enrolled in this course"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate price
    price = course.current_price
    discount_amount = 0
    coupon_obj = None
    
    # Apply coupon if provided
    if coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code=coupon_code.upper())
            if not coupon_obj.is_valid():
                return Response(
                    {"error": "Coupon is not valid or has expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if coupon applies to this course
            if coupon_obj.course and coupon_obj.course != course:
                return Response(
                    {"error": "Coupon is not valid for this course"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            discount_amount = coupon_obj.get_discount_amount(price)
            price = max(0, price - discount_amount)
            
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Handle free courses
    if price == 0 or course.is_free:
        # Create enrollment directly
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            price_paid=0,
            payment_method='free'
        )
        
        # Create transaction record
        Transaction.objects.create(
            transaction_id=f"FREE-{enrollment.id}",
            enrollment=enrollment,
            student=request.user,
            course=course,
            gross_amount=0,
            platform_fee=0,
            instructor_revenue=0,
            payment_method='free',
            status='completed'
        )
        
        return Response({
            "message": "Enrolled successfully",
            "enrollment_id": enrollment.id,
            "free": True
        })
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.title,
                        'description': course.subtitle or course.description[:100],
                        'images': [request.build_absolute_uri(course.thumbnail.url)] if course.thumbnail else [],
                    },
                    'unit_amount': int(price * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=settings.FRONTEND_URL + f'/courses/{course.slug}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=settings.FRONTEND_URL + f'/courses/{course.slug}/',
            client_reference_id=str(request.user.id),
            metadata={
                'course_id': course.id,
                'user_id': request.user.id,
                'coupon_code': coupon_code or '',
                'discount_amount': str(discount_amount),
            }
        )
        
        return Response({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except stripe.error.StripeError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def stripe_webhook(request):
    """
    Handle Stripe webhooks
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    return Response({'status': 'success'})


def handle_successful_payment(session):
    """
    Create enrollment and transaction after successful payment
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get data from session metadata
    course_id = session['metadata']['course_id']
    user_id = session['metadata']['user_id']
    coupon_code = session['metadata'].get('coupon_code', '')
    discount_amount = float(session['metadata'].get('discount_amount', 0))
    
    course = Course.objects.get(id=course_id)
    user = User.objects.get(id=user_id)
    
    # Check if enrollment already exists
    if Enrollment.objects.filter(student=user, course=course).exists():
        return
    
    # Calculate amounts
    gross_amount = session['amount_total'] / 100  # Convert from cents
    platform_fee_percent = settings.PLATFORM_FEE_PERCENT
    platform_fee = gross_amount * (platform_fee_percent / 100)
    instructor_revenue = gross_amount - platform_fee
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        student=user,
        course=course,
        price_paid=gross_amount,
        payment_method='stripe'
    )
    
    # Create transaction
    transaction = Transaction.objects.create(
        transaction_id=session['id'],
        enrollment=enrollment,
        student=user,
        course=course,
        gross_amount=gross_amount,
        platform_fee_percent=platform_fee_percent,
        platform_fee=platform_fee,
        instructor_revenue=instructor_revenue,
        payment_method='stripe',
        payment_provider_id=session['payment_intent'],
        coupon_code=coupon_code,
        discount_amount=discount_amount,
        status='completed'
    )
    
    # Update coupon usage
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code.upper())
            coupon.current_uses += 1
            coupon.save()
        except Coupon.DoesNotExist:
            pass
    
    # Update course stats
    course.update_stats()
    
    # Update instructor stats if profile exists
    if hasattr(course.instructor, 'instructor_profile'):
        course.instructor.instructor_profile.update_stats()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_coupon(request):
    """
    Validate and apply coupon to see discount
    POST: {
        "coupon_code": "SUMMER50",
        "course_id": 123
    }
    """
    code = request.data.get('coupon_code', '').upper()
    course_id = request.data.get('course_id')
    
    if not code:
        return Response(
            {"error": "Coupon code is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return Response(
            {"error": "Invalid coupon code"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate coupon
    if not coupon.is_valid():
        return Response(
            {"error": "Coupon has expired or reached usage limit"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get course if specified
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        
        # Check if coupon applies to this course
        if coupon.course and coupon.course != course:
            return Response(
                {"error": "Coupon is not valid for this course"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        original_price = course.current_price
        discount_amount = coupon.get_discount_amount(original_price)
        final_price = max(0, original_price - discount_amount)
        
        return Response({
            'valid': True,
            'coupon': {
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
            },
            'pricing': {
                'original_price': float(original_price),
                'discount_amount': float(discount_amount),
                'final_price': float(final_price),
                'savings_percent': round((discount_amount / original_price * 100) if original_price > 0 else 0, 2)
            }
        })
    
    return Response({
        'valid': True,
        'coupon': {
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchase_history(request):
    """
    Get user's purchase history
    """
    transactions = Transaction.objects.filter(
        student=request.user,
        status='completed'
    ).select_related('course').order_by('-created_at')
    
    history = []
    for transaction in transactions:
        history.append({
            'transaction_id': transaction.transaction_id,
            'course': {
                'title': transaction.course.title,
                'slug': transaction.course.slug,
                'instructor': transaction.course.instructor.get_full_name(),
            },
            'amount_paid': float(transaction.gross_amount),
            'payment_method': transaction.payment_method,
            'purchased_at': transaction.created_at,
        })
    
    return Response({
        'total_purchases': len(history),
        'total_spent': sum(float(t.gross_amount) for t in transactions),
        'purchases': history
    })
