"""
URL routing for Payment API
"""
from django.urls import path
from . import stripe_api

app_name = 'payments'

urlpatterns = [
    # Stripe checkout
    path('checkout/', stripe_api.create_checkout_session, name='checkout'),
    path('webhook/', stripe_api.stripe_webhook, name='stripe-webhook'),
    path('momo/webhook/', stripe_api.momo_webhook, name='momo-webhook'),
    
    # Coupons
    path('coupon/apply/', stripe_api.apply_coupon, name='apply-coupon'),
    
    # Purchase history
    path('history/', stripe_api.purchase_history, name='purchase-history'),
    path('orders/<str:order_number>/', stripe_api.get_order_detail, name='order-detail'),
]
