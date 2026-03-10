from adapters.base import PaymentGatewayAdapter, PaymentResult
import uuid
import logging

logger = logging.getLogger(__name__)


class MockPaymentGateway(PaymentGatewayAdapter):
    """
    Mock payment gateway.
    Replace with: StripePaymentGateway(api_key=os.environ['STRIPE_KEY'])
    """

    async def create_payment(self, amount: float, currency: str = "INR", metadata: dict = None) -> PaymentResult:
        ref = f"mock_pay_{uuid.uuid4().hex[:12]}"
        logger.info(f"[MOCK PAY] Created payment: {amount} {currency} → {ref}")
        return PaymentResult(
            success=True, reference=ref,
            message="Mock payment processed",
            metadata={"amount": amount, "currency": currency, **(metadata or {})}
        )

    async def process_refund(self, payment_reference: str, amount: float) -> PaymentResult:
        ref = f"mock_ref_{uuid.uuid4().hex[:12]}"
        logger.info(f"[MOCK PAY] Refund: {amount} for {payment_reference} → {ref}")
        return PaymentResult(success=True, reference=ref, message="Mock refund processed")

    async def get_payment_status(self, payment_reference: str) -> dict:
        logger.info(f"[MOCK PAY] Status check: {payment_reference}")
        return {"reference": payment_reference, "status": "completed", "provider": "mock"}

    async def create_payout(self, recipient_id: str, amount: float, currency: str = "INR") -> PaymentResult:
        ref = f"mock_payout_{uuid.uuid4().hex[:12]}"
        logger.info(f"[MOCK PAY] Payout: {amount} {currency} to {recipient_id} → {ref}")
        return PaymentResult(success=True, reference=ref, message="Mock payout processed")
