from adapters.base import MapServiceAdapter, GeoLocation, RouteInfo
from typing import List
import logging

logger = logging.getLogger(__name__)

# Known Ladakh locations for mock geocoding
LADAKH_LOCATIONS = {
    "leh": GeoLocation(34.1526, 77.5771, "Leh, Ladakh 194101"),
    "nubra": GeoLocation(34.6867, 77.5689, "Diskit, Nubra Valley, Ladakh"),
    "pangong": GeoLocation(33.7595, 78.6650, "Pangong Tso, Ladakh"),
    "turtuk": GeoLocation(34.8475, 76.8213, "Turtuk, Ladakh"),
    "khardung": GeoLocation(34.2818, 77.6025, "Khardung La Pass, Ladakh"),
    "changla": GeoLocation(34.0598, 77.8865, "Chang La Pass, Ladakh"),
    "hanle": GeoLocation(32.7794, 78.9760, "Hanle, Ladakh"),
    "lamayuru": GeoLocation(34.2839, 76.8125, "Lamayuru, Ladakh"),
}


class MockMapService(MapServiceAdapter):
    """Replace with: GoogleMapsService(api_key)"""

    async def geocode(self, address: str) -> GeoLocation:
        addr_lower = address.lower()
        for key, loc in LADAKH_LOCATIONS.items():
            if key in addr_lower:
                logger.info(f"[MOCK MAP] Geocode: {address} → {loc.lat},{loc.lng}")
                return loc
        default = GeoLocation(34.1526, 77.5771, address)
        logger.info(f"[MOCK MAP] Geocode default: {address} → Leh")
        return default

    async def reverse_geocode(self, lat: float, lng: float) -> GeoLocation:
        best_match = min(
            LADAKH_LOCATIONS.values(),
            key=lambda loc: abs(loc.lat - lat) + abs(loc.lng - lng)
        )
        logger.info(f"[MOCK MAP] Reverse: {lat},{lng} → {best_match.address}")
        return GeoLocation(lat, lng, best_match.address)

    async def calculate_route(self, origin: GeoLocation, destination: GeoLocation) -> RouteInfo:
        # Approximate distance using lat/lng difference
        dlat = abs(origin.lat - destination.lat)
        dlng = abs(origin.lng - destination.lng)
        distance_km = round((dlat + dlng) * 111, 1)  # ~111km per degree
        duration_min = round(distance_km / 30 * 60, 0)  # ~30 km/h average on mountain roads
        logger.info(f"[MOCK MAP] Route: {distance_km}km, {duration_min}min")
        return RouteInfo(
            distance_km=distance_km, duration_minutes=duration_min,
            polyline="mock_polyline", steps=[]
        )

    async def find_nearby(self, lat: float, lng: float, radius_km: float, category: str = "") -> List[GeoLocation]:
        results = []
        for loc in LADAKH_LOCATIONS.values():
            dlat = abs(loc.lat - lat)
            dlng = abs(loc.lng - lng)
            approx_dist = (dlat + dlng) * 111
            if approx_dist <= radius_km:
                results.append(loc)
        logger.info(f"[MOCK MAP] Nearby: {len(results)} found within {radius_km}km")
        return results
