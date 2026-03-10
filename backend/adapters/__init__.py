"""
Adapter registry — single source of truth for all integration instances.

To swap a mock for a real provider:
    from adapters.payment import StripePaymentGateway
    payment_gateway = StripePaymentGateway(api_key=os.environ['STRIPE_KEY'])

No changes needed in routes or services.
"""
from adapters.payment import MockPaymentGateway
from adapters.notification import MockSMSProvider, MockEmailProvider, MockPushProvider
from adapters.kyc import MockKYCProvider
from adapters.maps import MockMapService
from adapters.iot import MockIoTLockService

# ─── Active adapter instances ──────────────────────────────
payment_gateway = MockPaymentGateway()
sms_provider = MockSMSProvider()
email_provider = MockEmailProvider()
push_provider = MockPushProvider()
kyc_provider = MockKYCProvider()
map_service = MockMapService()
iot_lock_service = MockIoTLockService()
