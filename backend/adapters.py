import uuid


class PaymentResult:
    def __init__(self, success, reference, message=""):
        self.success = success
        self.reference = reference
        self.message = message


class MockPaymentGateway:
    """Mock payment gateway - replaceable with Stripe/Razorpay via adapter pattern"""

    async def create_payment(self, amount, currency="INR", metadata=None):
        return PaymentResult(
            success=True,
            reference=f"mock_pay_{uuid.uuid4().hex[:12]}",
            message="Mock payment processed successfully"
        )

    async def process_refund(self, payment_reference, amount):
        return PaymentResult(
            success=True,
            reference=f"mock_ref_{uuid.uuid4().hex[:12]}",
            message="Mock refund processed"
        )


class MockSMSProvider:
    """Mock SMS - replaceable with Twilio"""

    async def send_sms(self, phone, message):
        return {"success": True, "message_id": f"mock_sms_{uuid.uuid4().hex[:8]}"}


class MockEmailProvider:
    """Mock Email - replaceable with SendGrid"""

    async def send_email(self, to, subject, body):
        return {"success": True, "message_id": f"mock_email_{uuid.uuid4().hex[:8]}"}


class MockKYCProvider:
    """Mock KYC verification"""

    async def verify_identity(self, user_id, id_type, id_number):
        return {"verified": True, "verification_id": f"mock_kyc_{uuid.uuid4().hex[:8]}"}


class MockMapService:
    """Mock map service - replaceable with Google Maps"""

    async def geocode(self, address):
        return {"lat": 34.1526, "lng": 77.5771}

    async def calculate_distance(self, from_coords, to_coords):
        return {"distance_km": 15.5, "duration_minutes": 30}


class MockIoTLockService:
    """Mock IoT smart lock - replaceable with real IoT provider"""

    async def unlock(self, lock_id):
        return {"success": True, "lock_status": "unlocked"}

    async def lock(self, lock_id):
        return {"success": True, "lock_status": "locked"}

    async def get_status(self, lock_id):
        return {"lock_status": "locked", "battery": 85}


# Singleton instances
payment_gateway = MockPaymentGateway()
sms_provider = MockSMSProvider()
email_provider = MockEmailProvider()
kyc_provider = MockKYCProvider()
map_service = MockMapService()
iot_lock_service = MockIoTLockService()
