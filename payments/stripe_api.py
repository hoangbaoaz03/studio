import logging
import json
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from course.models import Course
from result.models import Enrollment
from payments.models import Order, OrderItem, Transaction, Coupon
from payments.providers.factory import get_provider

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Create checkout session for MULTIPLE course purchases
    Supports multiple providers (Stripe, MoMo)
    POST: {
        "course_ids": [123, 124],
        "coupon_code": "SUMMER50",
        "payment_method": "momo" | "stripe" (default)
    }
    """
    course_ids = request.data.get('course_ids', [])
    coupon_code = request.data.get('coupon_code')
    payment_method = request.data.get('payment_method', 'stripe')
    
    logger.info(f"Checkout initiated by {request.user.id} via {payment_method} for courses: {course_ids}")
    print(f"DEBUG: Payload received: {request.data}")
    
    if not course_ids or not isinstance(course_ids, list):
        print(f"DEBUG: Invalid course_ids: {course_ids}")
        return Response({"error": "course_ids list is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    # Validation & Order Creation Logic (Shared)
    # ------------------------------------------
    courses = Course.objects.filter(id__in=course_ids, status='published')
    if len(courses) != len(course_ids):
        found_ids = [c.id for c in courses]
        print(f"DEBUG: Course mismatch. Requested: {course_ids}, Found: {found_ids}")
        return Response({"error": "One or more courses not found"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check already enrolled
    already_enrolled = Enrollment.objects.filter(student=request.user, course__in=courses).values_list('course__title', flat=True)
    if already_enrolled:
        print(f"DEBUG: Already enrolled: {list(already_enrolled)}")
        return Response({"error": f"Already enrolled in: {', '.join(already_enrolled)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate Total
    total_amount = sum(c.current_price for c in courses)
    final_amount = total_amount # TODO: Apply coupon logic if needed
    
    # Create Pending Order
    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        final_amount=final_amount,
        status='pending'
    )
    
    for course in courses:
        OrderItem.objects.create(order=order, course=course, price=course.current_price)

    # Provider Delegation
    # -------------------
    try:
        provider = get_provider(payment_method)
        result = provider.create_payment(order, request)
        
        # Update Order with Session/Request ID
        order.payment_provider_session_id = result.get('session_id')
        order.save()
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Payment Provider Error: {str(e)}")
        order.status = 'failed'
        order.save()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def stripe_webhook(request):
    """Handle Stripe Webhooks"""
    provider = get_provider('stripe')
    data = provider.process_webhook(request)
    
    if data:
        # data is checkout.session object
        session = data
        if session.get('metadata', {}).get('type') == 'cart_checkout':
            order_id = session['metadata']['order_id']
            handle_payment_success(order_id, session['id'], 'stripe')
            
    return Response({'status': 'success'})


@api_view(['POST'])
def momo_webhook(request):
    """Handle MoMo IPN (Instant Payment Notification)"""
    try:
        provider = get_provider('momo')
        # MoMo sends JSON body
        data = json.loads(request.body)
        
        # Verify Signature
        is_valid, order_id, txn_id, msg = provider.verify_payment(data)
        
        if is_valid:
            handle_payment_success(order_id, txn_id, 'momo')
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            logger.error(f"MoMo Signature Invalid: {msg}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"MoMo Webhook Error: {str(e)}")
        return Response(status=status.HTTP_400_BAD_REQUEST)


def handle_payment_success(order_id, provider_txn_id, payment_method):
    """
    Shared logic to grant access after successful payment
    Atomic & Idempotent
    """
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(order_number=order_id) if isinstance(order_id, str) and order_id.startswith('ORD') else Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found during payment success processing")
            return

        if order.status == 'completed':
            logger.info(f"Order {order_id} already completed. Duplicate signal ignored.")
            return

        # Update Order
        order.status = 'completed'
        order.save()
        
        # Grant Access (Create Enrollments)
        for item in order.items.all():
            course = item.course
            if Enrollment.objects.filter(student=order.user, course=course).exists():
                continue
            
            # Financials
            gross_amount = item.price
            platform_fee_percent = settings.PLATFORM_FEE_PERCENT
            platform_fee = float(gross_amount) * (platform_fee_percent / 100)
            
            enrollment = Enrollment.objects.create(
                student=order.user,
                course=course,
                price_paid=gross_amount,
                payment_method=payment_method
            )
            
            Transaction.objects.create(
                transaction_id=f"{provider_txn_id}-{course.id}",
                enrollment=enrollment,
                student=order.user,
                course=course,
                gross_amount=gross_amount,
                platform_fee=platform_fee,
                instructor_revenue=float(gross_amount) - platform_fee,
                payment_method=payment_method,
                payment_provider_id=provider_txn_id,
                status='completed'
            )
            
            course.update_stats()
            # Update Instructor Stats
            if hasattr(course.instructor, 'instructor_profile'):
                course.instructor.instructor_profile.update_stats()
                
        logger.info(f"Successfully processed Order {order.order_number} via {payment_method}")

# ------------------------------------------------------------------
# Legacy / Shared Endpoints (Coupon, History) - Kept for compatibility
# ------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_coupon(request):
    # ... (Keep existing logic)
    code = request.data.get('coupon_code', '').upper()
    course_id = request.data.get('course_id')
    
    if not code:
        return Response({"error": "Coupon code is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return Response({"error": "Invalid coupon code"}, status=status.HTTP_404_NOT_FOUND)
    
    if not coupon.is_valid():
        return Response({"error": "Coupon has expired"}, status=status.HTTP_400_BAD_REQUEST)
        
    return Response({
        'valid': True,
        'coupon': {'code': coupon.code, 'discount_value': float(coupon.discount_value)}
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchase_history(request):
    transactions = Transaction.objects.filter(student=request.user, status='completed').order_by('-created_at')
    
    return Response({
        'total_purchases': transactions.count(),
        'purchases': [{
            'course': t.course.title,
            'amount': float(t.gross_amount),
            'date': t.created_at,
            'method': t.payment_method
        } for t in transactions]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_detail(request, order_number):
    """
    Get order details for confirmation page
    Used for selective cart clearing
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    items = []
    for item in order.items.all():
        items.append({
            'course_id': item.course.id,
            'title': item.course.title,
            'slug': item.course.slug,
            'price': item.price
        })
        
    return Response({
        'order_number': order.order_number,
        'status': order.status,
        'total_amount': order.total_amount,
        'purchased_course_ids': [item['course_id'] for item in items],
        'items': items
    })
