from adapters.base import SMSAdapter, EmailAdapter, PushNotificationAdapter, NotificationResult
from typing import List, Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class MockSMSProvider(SMSAdapter):
    """Replace with: TwilioSMSProvider(account_sid, auth_token, from_number)"""

    async def send_sms(self, phone: str, message: str) -> NotificationResult:
        mid = f"mock_sms_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK SMS] To: {phone} | {message[:60]}... → {mid}")
        return NotificationResult(success=True, message_id=mid, channel="sms")

    async def send_bulk_sms(self, recipients: List[Dict[str, str]]) -> List[NotificationResult]:
        results = []
        for r in recipients:
            res = await self.send_sms(r["phone"], r["message"])
            results.append(res)
        logger.info(f"[MOCK SMS] Bulk sent to {len(recipients)} recipients")
        return results


class MockEmailProvider(EmailAdapter):
    """Replace with: SendGridEmailProvider(api_key)"""

    async def send_email(self, to: str, subject: str, body: str, html: Optional[str] = None) -> NotificationResult:
        mid = f"mock_email_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK EMAIL] To: {to} | Subject: {subject} → {mid}")
        return NotificationResult(success=True, message_id=mid, channel="email")

    async def send_template_email(self, to: str, template_id: str, variables: dict) -> NotificationResult:
        mid = f"mock_tmpl_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK EMAIL] Template: {template_id} → {to} → {mid}")
        return NotificationResult(success=True, message_id=mid, channel="email")


class MockPushProvider(PushNotificationAdapter):
    """Replace with: FirebasePushProvider(credentials_path)"""

    async def send_push(self, device_token: str, title: str, body: str, data: Optional[dict] = None) -> NotificationResult:
        mid = f"mock_push_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK PUSH] Token: {device_token[:20]}... | {title} → {mid}")
        return NotificationResult(success=True, message_id=mid, channel="push")

    async def send_topic_push(self, topic: str, title: str, body: str, data: Optional[dict] = None) -> NotificationResult:
        mid = f"mock_topic_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MOCK PUSH] Topic: {topic} | {title} → {mid}")
        return NotificationResult(success=True, message_id=mid, channel="push")
