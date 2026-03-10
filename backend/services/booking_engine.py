"""
Booking Engine — core booking business logic.

Responsibilities:
  - Atomic double-booking prevention
  - Late return penalty calculation
  - Booking extension with availability check
  - Overdue booking detection (background scan)
  - Availability calendar generation
  - Booking cost calculation with weekly discounts
"""
from database import db
from pymongo import ReturnDocument
from datetime import datetime, timezone, timedelta
import math
import uuid
import logging

logger = logging.getLogger(__name__)

# ─── Configuration ──────────────────────────────────────────
GRACE_PERIOD_HOURS = 2
PENALTY_MULTIPLIER = 1.5
PLATFORM_COMMISSION_RATE = 0.10
CANCELLATION_WINDOW_HOURS = 24  # Free cancellation if > 24h before start


def calculate_booking_cost(daily_rate: float, weekly_rate: float, total_days: int) -> dict:
    """Calculate cost with weekly discount logic."""
    if total_days >= 7 and weekly_rate:
        weeks = total_days // 7
        remaining = total_days % 7
        base = (weeks * weekly_rate) + (remaining * daily_rate)
        discount = (total_days * daily_rate) - base
    else:
        base = total_days * daily_rate
        discount = 0
    return {"base_amount": base, "discount": discount, "daily_rate": daily_rate, "total_days": total_days}


def calculate_penalty(end_date_str: str, actual_return_str: str, daily_rate: float) -> dict:
    """Late return penalty: grace period, then multiplied daily rate per extra day."""
    end_date = datetime.fromisoformat(end_date_str)
    actual_return = datetime.fromisoformat(actual_return_str)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if actual_return.tzinfo is None:
        actual_return = actual_return.replace(tzinfo=timezone.utc)

    grace_deadline = end_date + timedelta(hours=GRACE_PERIOD_HOURS)
    if actual_return <= grace_deadline:
        return {"penalty": 0, "extra_days": 0, "is_late": False}

    extra_hours = (actual_return - end_date).total_seconds() / 3600
    extra_days = math.ceil(extra_hours / 24)
    penalty = extra_days * daily_rate * PENALTY_MULTIPLIER

    return {
        "penalty": penalty,
        "extra_days": extra_days,
        "extra_hours": round(extra_hours, 1),
        "is_late": True,
        "grace_period_hours": GRACE_PERIOD_HOURS,
        "penalty_rate": f"{PENALTY_MULTIPLIER}x daily rate"
    }


def calculate_cancellation_fee(booking: dict) -> dict:
    """Determine cancellation fee based on proximity to start date."""
    start = datetime.fromisoformat(booking["start_date"])
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    hours_until_start = (start - now).total_seconds() / 3600

    if hours_until_start > CANCELLATION_WINDOW_HOURS:
        return {"fee": 0, "refund_percent": 100, "reason": "Free cancellation (>24h before start)"}
    elif hours_until_start > 6:
        fee = booking["base_amount"] * 0.25
        return {"fee": fee, "refund_percent": 75, "reason": "25% cancellation fee (6-24h before start)"}
    else:
        fee = booking["base_amount"] * 0.50
        return {"fee": fee, "refund_percent": 50, "reason": "50% cancellation fee (<6h before start)"}


async def check_availability(bike_id: str, start_date: str, end_date: str) -> dict:
    """Check if a bike is available for given date range."""
    bike = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0, "booking_slots": 1, "is_available": 1})
    if not bike:
        return {"available": False, "reason": "Bike not found"}
    if not bike.get("is_available"):
        return {"available": False, "reason": "Bike marked unavailable by owner"}

    for slot in bike.get("booking_slots", []):
        if slot["status"] not in ["confirmed", "active"]:
            continue
        if slot["start_date"] < end_date and slot["end_date"] > start_date:
            return {
                "available": False,
                "reason": "Date conflict with existing booking",
                "conflicting_dates": {"start": slot["start_date"], "end": slot["end_date"]}
            }
    return {"available": True}


async def get_availability_calendar(bike_id: str, month: int, year: int) -> dict:
    """Generate a month-view availability calendar for a bike."""
    bike = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0, "booking_slots": 1, "is_available": 1, "daily_rate": 1})
    if not bike:
        return {"error": "Bike not found"}

    from calendar import monthrange
    _, num_days = monthrange(year, month)
    days = {}

    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        day_start = f"{date_str}T00:00:00"
        day_end = f"{date_str}T23:59:59"

        is_booked = False
        for slot in bike.get("booking_slots", []):
            if slot["status"] not in ["confirmed", "active"]:
                continue
            if slot["start_date"][:10] <= date_str and slot["end_date"][:10] >= date_str:
                is_booked = True
                break

        is_past = datetime(year, month, day, tzinfo=timezone.utc) < datetime.now(timezone.utc)
        days[date_str] = {
            "available": not is_booked and not is_past and bike.get("is_available", True),
            "booked": is_booked,
            "past": is_past,
            "rate": bike.get("daily_rate", 0)
        }

    return {
        "bike_id": bike_id,
        "month": month,
        "year": year,
        "days": days,
        "total_available": sum(1 for d in days.values() if d["available"]),
        "total_booked": sum(1 for d in days.values() if d["booked"])
    }


async def atomic_create_booking(bike_id: str, start_date: str, end_date: str, booking_id: str) -> bool:
    """Atomic double-booking prevention using findOneAndUpdate."""
    result = await db.bikes.find_one_and_update(
        {
            "bike_id": bike_id,
            "booking_slots": {
                "$not": {
                    "$elemMatch": {
                        "start_date": {"$lt": end_date},
                        "end_date": {"$gt": start_date},
                        "status": {"$in": ["confirmed", "active"]}
                    }
                }
            }
        },
        {
            "$push": {
                "booking_slots": {
                    "booking_id": booking_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": "confirmed"
                }
            }
        },
        return_document=ReturnDocument.AFTER
    )
    return result is not None


async def atomic_extend_booking(bike_id: str, booking_id: str, current_end: str, new_end: str) -> bool:
    """Atomic extension: check no conflict in the extension window, then extend."""
    result = await db.bikes.find_one_and_update(
        {
            "bike_id": bike_id,
            "booking_slots": {
                "$not": {
                    "$elemMatch": {
                        "booking_id": {"$ne": booking_id},
                        "start_date": {"$lt": new_end},
                        "end_date": {"$gt": current_end},
                        "status": {"$in": ["confirmed", "active"]}
                    }
                }
            }
        },
        {"$set": {"booking_slots.$[elem].end_date": new_end}},
        array_filters=[{"elem.booking_id": booking_id}],
        return_document=ReturnDocument.AFTER
    )
    return result is not None


async def scan_overdue_bookings() -> int:
    """Scan for bookings past their end_date and mark as overdue. Returns count."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.bookings.update_many(
        {
            "status": "active",
            "end_date": {"$lt": now}
        },
        {"$set": {"status": "overdue", "updated_at": now}}
    )
    count = result.modified_count

    if count > 0:
        logger.warning(f"[OVERDUE SCAN] Marked {count} bookings as overdue")
        # Update bike slots too
        overdue_bookings = await db.bookings.find({"status": "overdue"}, {"_id": 0, "booking_id": 1, "bike_id": 1}).to_list(100)
        for b in overdue_bookings:
            await db.bikes.update_one(
                {"bike_id": b["bike_id"], "booking_slots.booking_id": b["booking_id"]},
                {"$set": {"booking_slots.$.status": "overdue"}}
            )
    return count


VALID_STATUS_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["active", "cancelled"],
    "active": ["completed", "overdue"],
    "overdue": ["completed"],
}


def validate_status_transition(current: str, target: str) -> bool:
    return target in VALID_STATUS_TRANSITIONS.get(current, [])
