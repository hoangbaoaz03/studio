import json
import uuid
import hmac
import hashlib
import requests
from django.conf import settings
from .base import PaymentProvider
import logging

logger = logging.getLogger(__name__)

class MoMoProvider(PaymentProvider):
    def __init__(self):
        self.partner_code = settings.MOMO_PARTNER_CODE
        self.access_key = settings.MOMO_ACCESS_KEY
        self.secret_key = settings.MOMO_SECRET_KEY
        self.endpoint = settings.MOMO_ENDPOINT
        self.return_url = settings.MOMO_RETURN_URL
        self.notify_url = settings.MOMO_NOTIFY_URL

    def create_payment(self, order, request):
        order_id = str(order.order_number)
        request_id = str(uuid.uuid4())
        amount = str(int(order.final_amount)) # MoMo requires integer string
        order_info = f"Payment for Order {order_id}"
        request_type = "captureWallet"
        extra_data = "" # base64 encode if needed, empty for now

        # Raw Signature string construction (Specific order required by MoMo)
        # accessKey=$accessKey&amount=$amount&extraData=$extraData&ipnUrl=$ipnUrl&orderId=$orderId&orderInfo=$orderInfo&partnerCode=$partnerCode&redirectUrl=$redirectUrl&requestId=$requestId&requestType=$requestType
        raw_signature = (
            f"accessKey={self.access_key}"
            f"&amount={amount}"
            f"&extraData={extra_data}"
            f"&ipnUrl={self.notify_url}"
            f"&orderId={order_id}"
            f"&orderInfo={order_info}"
            f"&partnerCode={self.partner_code}"
            f"&redirectUrl={self.return_url}"
            f"&requestId={request_id}"
            f"&requestType={request_type}"
        )

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_signature.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        payload = {
            'partnerCode': self.partner_code,
            'partnerName': "SkyLearn",
            'storeId': "MomoStore",
            'requestId': request_id,
            'amount': amount,
            'orderId': order_id,
            'orderInfo': order_info,
            'redirectUrl': self.return_url,
            'ipnUrl': self.notify_url,
            'lang': 'vi',
            'extraData': extra_data,
            'requestType': request_type,
            'signature': signature
        }

        try:
            response = requests.post(self.endpoint, json=payload)
            data = response.json()
            
            if data.get('resultCode') == 0:
                return {
                    'payment_url': data['payUrl'],
                    'session_id': request_id, # Use request_id as session ref
                    'order_id': order.order_number
                }
            else:
                logger.error(f"MoMo Creation Error: {data}")
                raise Exception(f"MoMo Error: {data.get('message')}")
                
        except Exception as e:
            logger.error(f"MoMo Connect Error: {str(e)}")
            raise e

    def verify_payment(self, data):
        # Verify signature from return URL params or IPN body
        # data is a dict of params
        
        # Required fields for signature
        access_key = data.get('accessKey')
        amount = data.get('amount')
        extra_data = data.get('extraData')
        message = data.get('message')
        order_id = data.get('orderId')
        order_info = data.get('orderInfo')
        order_type = data.get('orderType')
        partner_code = data.get('partnerCode')
        pay_type = data.get('payType')
        request_id = data.get('requestId')
        response_time = data.get('responseTime')
        result_code = data.get('resultCode')
        trans_id = data.get('transId')
        signature = data.get('signature')

        # Raw String for Response
        # accessKey=$accessKey&amount=$amount&extraData=$extraData&message=$message&orderId=$orderId&orderInfo=$orderInfo&orderType=$orderType&partnerCode=$partnerCode&payType=$payType&requestId=$requestId&responseTime=$responseTime&resultCode=$resultCode&transId=$transId
        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={amount}"
            f"&extraData={extra_data}"
            f"&message={message}"
            f"&orderId={order_id}"
            f"&orderInfo={order_info}"
            f"&orderType={order_type}"
            f"&partnerCode={partner_code}"
            f"&payType={pay_type}"
            f"&requestId={request_id}"
            f"&responseTime={response_time}"
            f"&resultCode={result_code}"
            f"&transId={trans_id}"
        )

        my_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_signature.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if my_signature != signature:
             return False, order_id, trans_id, "Invalid Signature"
        
        if str(result_code) == '0':
            return True, order_id, trans_id, "Success"
            
        return False, order_id, trans_id, f"Failed with code {result_code}"

    def process_webhook(self, request):
        # For MoMo, webhook payload is JSON body
        try:
            return json.loads(request.body)
        except:
            return request.POST.dict() 
