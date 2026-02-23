from abc import ABC, abstractmethod

class PaymentProvider(ABC):
    """
    Abstract base class for payment providers (Stripe, MoMo, ZaloPay, etc.)
    """
    
    @abstractmethod
    def create_payment(self, order, request):
        """
        Create a payment session/request
        Returns:
            dict: {
                'payment_url': str,   # Redirect URL for user
                'session_id': str,    # Provider session ID
                'order_id': str       # Internal Order ID
            }
        """
        pass
    
    @abstractmethod
    def verify_payment(self, data):
        """
        Verify payment data (webhook or return URL)
        Returns:
            tuple: (is_success, order_id, transaction_id, message)
        """
        pass
    
    @abstractmethod
    def process_webhook(self, request):
        """
        Handle asynchronous webhook notifications
        """
        pass
