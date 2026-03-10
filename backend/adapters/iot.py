from adapters.base import IoTLockAdapter, LockStatus, GeoLocation
from typing import Dict, Any
import uuid
import logging

logger = logging.getLogger(__name__)


class MockIoTLockService(IoTLockAdapter):
    """Replace with: SmartLockProvider(api_key, hub_url)"""

    # In-memory state for mock locks
    _locks: Dict[str, dict] = {}

    def _get_lock(self, lock_id: str) -> dict:
        if lock_id not in self._locks:
            self._locks[lock_id] = {
                "status": "locked", "battery": 85,
                "lat": 34.1526, "lng": 77.5771,
                "total_km": 0
            }
        return self._locks[lock_id]

    async def unlock(self, lock_id: str, user_id: str) -> LockStatus:
        lock = self._get_lock(lock_id)
        lock["status"] = "unlocked"
        logger.info(f"[MOCK IOT] Unlock: {lock_id} by {user_id}")
        return LockStatus(
            lock_id=lock_id, status="unlocked",
            battery_percent=lock["battery"], last_seen="now"
        )

    async def lock(self, lock_id: str, user_id: str) -> LockStatus:
        lock = self._get_lock(lock_id)
        lock["status"] = "locked"
        logger.info(f"[MOCK IOT] Lock: {lock_id} by {user_id}")
        return LockStatus(
            lock_id=lock_id, status="locked",
            battery_percent=lock["battery"], last_seen="now"
        )

    async def get_status(self, lock_id: str) -> LockStatus:
        lock = self._get_lock(lock_id)
        return LockStatus(
            lock_id=lock_id, status=lock["status"],
            battery_percent=lock["battery"], last_seen="now",
            location=GeoLocation(lock["lat"], lock["lng"])
        )

    async def get_trip_data(self, lock_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
        logger.info(f"[MOCK IOT] Trip data: {lock_id} from {start_time} to {end_time}")
        return {
            "lock_id": lock_id,
            "distance_km": 145.3,
            "max_speed_kmh": 65,
            "avg_speed_kmh": 32,
            "idle_minutes": 120,
            "route_points": [
                {"lat": 34.1526, "lng": 77.5771, "ts": start_time},
                {"lat": 34.2818, "lng": 77.6025, "ts": end_time}
            ]
        }

    async def set_geofence(self, lock_id: str, center_lat: float, center_lng: float, radius_km: float) -> bool:
        logger.info(f"[MOCK IOT] Geofence: {lock_id} at {center_lat},{center_lng} r={radius_km}km")
        return True
