import stripe
from django.conf import settings
from .base import PaymentProvider

class StripeProvider(PaymentProvider):
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment(self, order, request):
        line_items = []
        for item in order.items.all():
            price = item.price
            if price > 0:
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.course.title,
                            # 'images': ... (optional)
                        },
                        'unit_amount': int(price * 100),
                    },
                    'quantity': 1,
                })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=settings.FRONTEND_URL + f'/checkout/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=settings.FRONTEND_URL + '/checkout/',
            client_reference_id=str(request.user.id),
            metadata={
                'order_id': order.id,
                'user_id': request.user.id,
                'type': 'cart_checkout' 
            }
        )
        
        return {
            'payment_url': checkout_session.url,
            'session_id': checkout_session.id,
            'order_id': order.order_number
        }

    def verify_payment(self, data):
        # Stripe verification is usually done via Webhook or retrieving session
        # For return URL verification (if needed):
        session_id = data.get('session_id')
        if not session_id:
            return False, None, None, "Missing session_id"
            
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                 order_id = session['metadata'].get('order_id')
                 txn_id = session.get('payment_intent')
                 return True, order_id, txn_id, "Payment successful"
        except Exception as e:
            return False, None, None, str(e)
            
        return False, None, None, "Payment not completed"

    def process_webhook(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return None # Invalid payload
        except stripe.error.SignatureVerificationError:
            return None # Invalid signature
            
        if event['type'] == 'checkout.session.completed':
            return event['data']['object']
            
        return None
