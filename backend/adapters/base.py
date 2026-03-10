"""
Adapter Layer - Abstract Base Classes

All external integrations implement these interfaces.
Swap mock → real provider by changing the class instantiation.
No business logic changes required.

Providers:
  Payment  → Stripe / Razorpay
  SMS      → Twilio
  Email    → SendGrid
  Push     → Firebase
  KYC      → DigiLocker / Aadhaar
  Maps     → Google Maps
  IoT Lock → Custom hardware
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


# ─── Payment Gateway ───────────────────────────────────────

@dataclass
class PaymentResult:
    success: bool
    reference: str
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class PaymentGatewayAdapter(ABC):
    @abstractmethod
    async def create_payment(self, amount: float, currency: str, metadata: dict) -> PaymentResult:
        """Charge customer for booking/penalty/extension"""

    @abstractmethod
    async def process_refund(self, payment_reference: str, amount: float) -> PaymentResult:
        """Refund a completed payment"""

    @abstractmethod
    async def get_payment_status(self, payment_reference: str) -> Dict[str, Any]:
        """Check status of a payment by reference"""

    @abstractmethod
    async def create_payout(self, recipient_id: str, amount: float, currency: str) -> PaymentResult:
        """Send payout to shop owner bank account"""


# ─── Notification Adapters ──────────────────────────────────

@dataclass
class NotificationResult:
    success: bool
    message_id: str
    channel: str
    error: str = ""


class SMSAdapter(ABC):
    @abstractmethod
    async def send_sms(self, phone: str, message: str) -> NotificationResult:
        """Send SMS to phone number"""

    @abstractmethod
    async def send_bulk_sms(self, recipients: List[Dict[str, str]]) -> List[NotificationResult]:
        """Send bulk SMS. Each recipient: {phone, message}"""


class EmailAdapter(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str, html: Optional[str] = None) -> NotificationResult:
        """Send email"""

    @abstractmethod
    async def send_template_email(self, to: str, template_id: str, variables: dict) -> NotificationResult:
        """Send email using a pre-defined template"""


class PushNotificationAdapter(ABC):
    @abstractmethod
    async def send_push(self, device_token: str, title: str, body: str, data: Optional[dict] = None) -> NotificationResult:
        """Send push notification to a single device"""

    @abstractmethod
    async def send_topic_push(self, topic: str, title: str, body: str, data: Optional[dict] = None) -> NotificationResult:
        """Send push notification to all subscribers of a topic"""


# ─── KYC Verification ──────────────────────────────────────

@dataclass
class KYCResult:
    verified: bool
    verification_id: str
    status: str  # pending, verified, rejected, expired
    details: Dict[str, Any] = field(default_factory=dict)


class KYCAdapter(ABC):
    @abstractmethod
    async def submit_verification(self, user_id: str, id_type: str, id_number: str, name: str, dob: str = "") -> KYCResult:
        """Submit identity for verification"""

    @abstractmethod
    async def get_verification_status(self, verification_id: str) -> KYCResult:
        """Check status of a pending verification"""

    @abstractmethod
    async def revoke_verification(self, verification_id: str) -> bool:
        """Revoke a completed verification"""


# ─── Map Service ───────────────────────────────────────────

@dataclass
class GeoLocation:
    lat: float
    lng: float
    address: str = ""
    place_id: str = ""


@dataclass
class RouteInfo:
    distance_km: float
    duration_minutes: float
    polyline: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)


class MapServiceAdapter(ABC):
    @abstractmethod
    async def geocode(self, address: str) -> GeoLocation:
        """Convert address to coordinates"""

    @abstractmethod
    async def reverse_geocode(self, lat: float, lng: float) -> GeoLocation:
        """Convert coordinates to address"""

    @abstractmethod
    async def calculate_route(self, origin: GeoLocation, destination: GeoLocation) -> RouteInfo:
        """Get driving route between two points"""

    @abstractmethod
    async def find_nearby(self, lat: float, lng: float, radius_km: float, category: str = "") -> List[GeoLocation]:
        """Find nearby places (shops, fuel stations, etc.)"""


# ─── IoT Smart Lock ────────────────────────────────────────

@dataclass
class LockStatus:
    lock_id: str
    status: str  # locked, unlocked, error, offline
    battery_percent: int = 0
    last_seen: str = ""
    location: Optional[GeoLocation] = None


class IoTLockAdapter(ABC):
    @abstractmethod
    async def unlock(self, lock_id: str, user_id: str) -> LockStatus:
        """Unlock a bike for authorized user"""

    @abstractmethod
    async def lock(self, lock_id: str, user_id: str) -> LockStatus:
        """Lock a bike"""

    @abstractmethod
    async def get_status(self, lock_id: str) -> LockStatus:
        """Get current lock status, battery, and location"""

    @abstractmethod
    async def get_trip_data(self, lock_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Get trip telemetry: distance, speed, route"""

    @abstractmethod
    async def set_geofence(self, lock_id: str, center_lat: float, center_lng: float, radius_km: float) -> bool:
        """Set geofence alert boundary"""
