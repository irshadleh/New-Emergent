from adapters.base import KYCAdapter, KYCResult
import uuid
import logging

logger = logging.getLogger(__name__)


class MockKYCProvider(KYCAdapter):
    """Replace with: DigiLockerKYCProvider(api_key, client_id)"""

    async def submit_verification(self, user_id: str, id_type: str, id_number: str, name: str, dob: str = "") -> KYCResult:
        vid = f"mock_kyc_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK KYC] Submit: user={user_id}, type={id_type} → {vid}")
        return KYCResult(
            verified=True, verification_id=vid, status="verified",
            details={"id_type": id_type, "name": name, "provider": "mock"}
        )

    async def get_verification_status(self, verification_id: str) -> KYCResult:
        logger.info(f"[MOCK KYC] Status check: {verification_id}")
        return KYCResult(verified=True, verification_id=verification_id, status="verified")

    async def revoke_verification(self, verification_id: str) -> bool:
        logger.info(f"[MOCK KYC] Revoke: {verification_id}")
        return True
