import logging
import uuid
from django.conf import settings
from .base import PaymentProvider

logger = logging.getLogger(__name__)

class MockMoMoProvider(PaymentProvider):
    """
    Mock Provider for MoMo to enable local development/testing without credentials
    """
    def __init__(self):
        self.return_url = settings.MOMO_RETURN_URL
        self.notify_url = settings.MOMO_NOTIFY_URL

    def create_payment(self, order, request):
        logger.info(f"MOCK MOMO: Creating payment for Order {order.order_number}")
        
        request_id = str(uuid.uuid4())
        
        # Instead of calling MoMo API, we generate a link to our local Mock Page
        # We assume the frontend has a page at /momo/mock-pay
        # We append params so the mock page knows what to display
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        pay_url = f"{frontend_url}/momo/mock-pay?orderId={order.order_number}&amount={int(order.final_amount)}&requestId={request_id}"
        
        return {
            'payment_url': pay_url,
            'session_id': request_id,
            'order_id': order.order_number
        }

    def verify_payment(self, data):
        """
        Verify the mock webhook payload
        """
        logger.info(f"MOCK MOMO: Verifying data: {data}")
        
        order_id = data.get('orderId')
        result_code = data.get('resultCode')
        message = data.get('message', '')
        trans_id = data.get('transId', 'MOCK_TRANS_ID')
        
        if str(result_code) == '0':
            return True, order_id, trans_id, "Mock Success"
            
        return False, order_id, trans_id, f"Mock Failed: {message}"

    def process_webhook(self, request):
        import json
        try:
            return json.loads(request.body)
        except:
            return request.POST.dict()
