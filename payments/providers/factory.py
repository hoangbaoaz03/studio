from .stripe import StripeProvider
from .momo import MoMoProvider
from .mock_momo import MockMoMoProvider
from django.conf import settings

def get_provider(name='stripe'):
    if name == 'momo':
        # Check if we should use Mock Provider
        # We can control this via settings.MOMO_IS_MOCK or generic PAYMENT_MODE
        # Per user request, check PAYMENT_PROVIDER or specific Momo Mock flag
        if getattr(settings, 'USE_MOCK_MOMO', False):
            return MockMoMoProvider()
        return MoMoProvider()
        
    elif name == 'mock_momo':
        return MockMoMoProvider()
        
    elif name == 'stripe':
        return StripeProvider()
    else:
        raise ValueError(f"Unknown payment provider: {name}")
