from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import json
import hmac
import hashlib
from payments.providers.momo import MoMoProvider
from payments.models import Order
from django.contrib.auth import get_user_model
from course.models import Course, Category

User = get_user_model()

from django.test import TestCase, override_settings

@override_settings(
    MOMO_PARTNER_CODE='MOMO_TEST',
    MOMO_ACCESS_KEY='ACCESS_TEST',
    MOMO_SECRET_KEY='SECRET_TEST',
    MOMO_ENDPOINT='https://test-payment.momo.vn/v2/gateway/api/create',
    MOMO_RETURN_URL='http://localhost:3000/checkout/success',
    MOMO_NOTIFY_URL='http://localhost:8000/api/payments/momo/webhook/'
)
class MoMoPaymentTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=self.user)
        
        self.category = Category.objects.create(name='Test Category', slug='test-cat')
        self.course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            price=10.0,
            status='published',
            category=self.category,
            instructor=self.user
        )
        
    @patch('requests.post')
    def test_create_momo_payment(self, mock_post):
        # Mock MoMo Response
        mock_response = Mock()
        mock_response.json.return_value = {
            'resultCode': 0,
            'payUrl': 'https://test-payment.momo.vn/pay',
            'requestId': 'req-123'
        }
        mock_post.return_value = mock_response
        
        payload = {
            'course_ids': [self.course.id],
            'payment_method': 'momo'
        }
        
        response = self.client.post('/api/payments/checkout/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['payment_url'], 'https://test-payment.momo.vn/pay')
        self.assertTrue(Order.objects.exists())
        # The session ID is a UUID, so just check it exists
        self.assertTrue(Order.objects.first().payment_provider_session_id)

    def test_momo_signature_verification(self):
        provider = MoMoProvider()
        
        # Create a valid signature manually
        raw_data = {
            'accessKey': provider.access_key,
            'amount': '100000',
            'extraData': '',
            'message': 'Success',
            'orderId': 'ORD-123',
            'orderInfo': 'Info',
            'orderType': 'momo_wallet',
            'partnerCode': provider.partner_code,
            'payType': 'qr',
            'requestId': 'req-123',
            'responseTime': '1234567890',
            'resultCode': '0',
            'transId': '123456'
        }
        
        raw_signature = (
            f"accessKey={raw_data['accessKey']}&amount={raw_data['amount']}&extraData={raw_data['extraData']}"
            f"&message={raw_data['message']}&orderId={raw_data['orderId']}&orderInfo={raw_data['orderInfo']}"
            f"&orderType={raw_data['orderType']}&partnerCode={raw_data['partnerCode']}&payType={raw_data['payType']}"
            f"&requestId={raw_data['requestId']}&responseTime={raw_data['responseTime']}"
            f"&resultCode={raw_data['resultCode']}&transId={raw_data['transId']}"
        )
        
        signature = hmac.new(
            provider.secret_key.encode('utf-8'),
            raw_signature.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        raw_data['signature'] = signature
        
        is_valid, _, _, _ = provider.verify_payment(raw_data)
        self.assertTrue(is_valid)
        
        # Test Invalid Signature
        raw_data['signature'] = 'invalid_sig'
        is_valid, _, _, _ = provider.verify_payment(raw_data)
        self.assertFalse(is_valid)

    @patch('payments.providers.momo.MoMoProvider.verify_payment')
    def test_momo_webhook_success(self, mock_verify):
        # Setup existing order
        order = Order.objects.create(
            user=self.user,
            total_amount=10.0,
            final_amount=10.0,
            order_number='ORD-123',
            status='pending'
        )
        
        mock_verify.return_value = (True, 'ORD-123', 'TRANS-123', 'Success')
        
        data = {'test': 'data'} # Payload doesn't matter as we mock verify
        response = self.client.post(
            '/api/payments/providers/momo/return/',  # Wait, I didn't add this URL yet!
             # I added momo_webhook but didn't register it in urls.py?
             # I need to check urls.py before running this.
             data,
             format='json'
        )
        # Ah, I haven't added the URL yet. I need to do that first.
