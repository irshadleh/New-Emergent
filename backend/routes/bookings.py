from fastapi import APIRouter, HTTPException, Request
from database import db
from models import BookingCreate
from routes.auth import get_current_user
from adapters import payment_gateway
from services.booking_engine import (
    calculate_booking_cost, calculate_penalty, calculate_cancellation_fee,
    check_availability, get_availability_calendar, atomic_create_booking,
    atomic_extend_booking, scan_overdue_bookings, validate_status_transition,
    PLATFORM_COMMISSION_RATE
)
from services.notification_engine import dispatch_notification, create_in_app_notification
from services.payout_engine import create_payout_entry
import uuid
from datetime import datetime, timezone, timedelta
from pymongo import ReturnDocument
import math
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["bookings"])


@router.get("/availability/{bike_id}")
async def bike_availability(bike_id: str, month: int = None, year: int = None):
    """Get availability calendar for a bike."""
    if not month or not year:
        now = datetime.now(timezone.utc)
        month = month or now.month
        year = year or now.year
    return await get_availability_calendar(bike_id, month, year)


@router.get("/availability/{bike_id}/check")
async def check_bike_availability(bike_id: str, start_date: str, end_date: str):
    """Check if a bike is available for specific dates."""
    return await check_availability(bike_id, start_date, end_date)


@router.post("/bookings/scan-overdue")
async def trigger_overdue_scan(request: Request):
    """Admin/background trigger: scan and mark overdue bookings."""
    count = await scan_overdue_bookings()
    return {"overdue_marked": count}


@router.post("/bookings")
async def create_booking(data: BookingCreate, request: Request):
    user = await get_current_user(request)

    bike = await db.bikes.find_one({"bike_id": data.bike_id}, {"_id": 0})
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")
    if not bike.get("is_available", False):
        raise HTTPException(status_code=400, detail="Bike is not available")

    start = datetime.fromisoformat(data.start_date)
    end = datetime.fromisoformat(data.end_date)
    if end <= start:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    total_days = max(1, (end - start).days)

    # Use service for cost calculation
    cost = calculate_booking_cost(bike["daily_rate"], bike.get("weekly_rate", 0), total_days)
    base_amount = cost["base_amount"]
    daily_rate = bike["daily_rate"]

    booking_id = f"booking_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    # ATOMIC DOUBLE-BOOKING PREVENTION via service
    booked = await atomic_create_booking(data.bike_id, data.start_date, data.end_date, booking_id)
    if not booked:
        raise HTTPException(
            status_code=409,
            detail="Bike is not available for the selected dates"
        )

    shop = await db.bike_shops.find_one({"shop_id": bike["shop_id"]}, {"_id": 0, "name": 1, "owner_id": 1})

    # Handle referral tracking
    referred_by = data.notes if data.notes and data.notes.startswith("REF-") else None

    booking_doc = {
        "booking_id": booking_id, "bike_id": data.bike_id,
        "shop_id": bike["shop_id"], "customer_id": user["user_id"],
        "bike_name": bike["name"], "shop_name": shop["name"] if shop else "",
        "start_date": data.start_date, "end_date": data.end_date,
        "actual_return_date": None, "status": "confirmed",
        "daily_rate": daily_rate, "total_days": total_days,
        "base_amount": base_amount, "penalty_amount": 0,
        "extension_amount": 0, "total_amount": base_amount,
        "payment_status": "pending", "notes": data.notes,
        "referred_by": referred_by,
        "created_at": now, "updated_at": now
    }
    await db.bookings.insert_one(booking_doc)

    # Payment via adapter
    pay_result = await payment_gateway.create_payment(base_amount, "INR", {"booking_id": booking_id})
    await db.payments.insert_one({
        "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
        "booking_id": booking_id, "user_id": user["user_id"],
        "amount": base_amount, "currency": "INR", "type": "booking",
        "status": "completed" if pay_result.success else "failed",
        "payment_method": "mock_gateway",
        "gateway_reference": pay_result.reference,
        "created_at": now
    })

    if pay_result.success:
        await db.bookings.update_one(
            {"booking_id": booking_id}, {"$set": {"payment_status": "paid"}}
        )
        booking_doc["payment_status"] = "paid"

    # Payout ledger via service
    await create_payout_entry(bike["shop_id"], booking_id, base_amount)

    # Smart notifications via engine
    variables = {
        "bike_name": bike["name"], "start_date": data.start_date[:10],
        "end_date": data.end_date[:10], "shop_name": shop["name"] if shop else "",
        "customer_name": user["name"], "total_amount": str(base_amount)
    }
    await dispatch_notification(user["user_id"], "booking_confirmed", variables, {"booking_id": booking_id})
    if shop:
        await dispatch_notification(shop["owner_id"], "new_booking", variables, {"booking_id": booking_id})

    result_doc = {k: v for k, v in booking_doc.items() if k != "_id"}
    return result_doc


@router.get("/bookings")
async def list_bookings(request: Request, status: str = None, role: str = None):
    user = await get_current_user(request)

    if user["role"] == "shop_owner" and role == "owner":
        shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
        if not shop:
            return {"bookings": []}
        query = {"shop_id": shop["shop_id"]}
    else:
        query = {"customer_id": user["user_id"]}

    if status:
        query["status"] = status

    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)

    for booking in bookings:
        bike = await db.bikes.find_one(
            {"bike_id": booking["bike_id"]},
            {"_id": 0, "name": 1, "images": 1, "type": 1}
        )
        if bike:
            booking["bike_name"] = bike.get("name", "")
            booking["bike_images"] = bike.get("images", [])
            booking["bike_type"] = bike.get("type", "")
        if user["role"] == "shop_owner" and role == "owner":
            customer = await db.users.find_one(
                {"user_id": booking["customer_id"]},
                {"_id": 0, "name": 1, "email": 1, "phone": 1}
            )
            if customer:
                booking["customer_name"] = customer.get("name", "")
                booking["customer_email"] = customer.get("email", "")

    return {"bookings": bookings}


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str, request: Request):
    user = await get_current_user(request)
    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != user["user_id"]:
        shop = await db.bike_shops.find_one({"shop_id": booking["shop_id"]}, {"_id": 0})
        if not shop or shop["owner_id"] != user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized")
    return booking


@router.put("/bookings/{booking_id}/status")
async def update_booking_status(booking_id: str, request: Request):
    user = await get_current_user(request)
    body = await request.json()
    new_status = body.get("status")

    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    valid_transitions = {
        "confirmed": ["active", "cancelled"],
        "active": ["completed", "overdue"],
        "overdue": ["completed"],
        "pending": ["confirmed", "cancelled"]
    }
    current = booking["status"]
    if not validate_status_transition(current, new_status):
        raise HTTPException(status_code=400, detail=f"Cannot transition from {current} to {new_status}")

    now = datetime.now(timezone.utc).isoformat()
    update = {"status": new_status, "updated_at": now}

    if new_status == "cancelled":
        await db.bikes.update_one(
            {"bike_id": booking["bike_id"]},
            {"$pull": {"booking_slots": {"booking_id": booking_id}}}
        )
    else:
        await db.bikes.update_one(
            {"bike_id": booking["bike_id"], "booking_slots.booking_id": booking_id},
            {"$set": {"booking_slots.$.status": new_status}}
        )

    await db.bookings.update_one({"booking_id": booking_id}, {"$set": update})

    await create_in_app_notification(
        booking["customer_id"], f"booking_{new_status}",
        f"Booking {new_status.replace('_', ' ').title()}",
        f"Your booking #{booking_id[-8:]} is now {new_status}",
        {"booking_id": booking_id}
    )
    return {"message": f"Booking updated to {new_status}"}


@router.post("/bookings/{booking_id}/return")
async def return_bike(booking_id: str, request: Request):
    user = await get_current_user(request)
    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["status"] not in ["active", "overdue", "confirmed"]:
        raise HTTPException(status_code=400, detail="Booking cannot be returned in current state")

    now = datetime.now(timezone.utc).isoformat()
    penalty_info = calculate_penalty(booking["end_date"], now, booking["daily_rate"])
    penalty = penalty_info["penalty"]

    update = {
        "status": "completed", "actual_return_date": now,
        "penalty_amount": penalty,
        "total_amount": booking["base_amount"] + penalty + booking.get("extension_amount", 0),
        "updated_at": now
    }
    await db.bookings.update_one({"booking_id": booking_id}, {"$set": update})

    await db.bikes.update_one(
        {"bike_id": booking["bike_id"], "booking_slots.booking_id": booking_id},
        {"$set": {"booking_slots.$.status": "completed"}}
    )

    if penalty > 0:
        pay_result = await payment_gateway.create_payment(penalty, "INR")
        await db.payments.insert_one({
            "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
            "booking_id": booking_id, "user_id": booking["customer_id"],
            "amount": penalty, "currency": "INR", "type": "penalty",
            "status": "completed", "payment_method": "mock_gateway",
            "gateway_reference": pay_result.reference, "created_at": now
        })
        await dispatch_notification(booking["customer_id"], "penalty_applied", {
            "penalty_amount": str(penalty), "bike_name": booking.get("bike_name", ""),
            "extra_days": str(penalty_info.get("extra_days", 0)), "customer_name": ""
        }, {"booking_id": booking_id, "penalty": penalty})

    await dispatch_notification(booking["customer_id"], "booking_completed", {
        "bike_name": booking.get("bike_name", ""), "customer_name": "",
        "total_amount": str(update["total_amount"])
    }, {"booking_id": booking_id})
    return {
        "message": "Bike returned", "penalty": penalty,
        "penalty_details": penalty_info,
        "total_amount": update["total_amount"]
    }


@router.post("/bookings/{booking_id}/extend")
async def extend_booking(booking_id: str, request: Request):
    user = await get_current_user(request)
    body = await request.json()
    new_end_date = body.get("new_end_date")

    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if booking["status"] not in ["confirmed", "active"]:
        raise HTTPException(status_code=400, detail="Cannot extend this booking")

    extended = await atomic_extend_booking(booking["bike_id"], booking_id, booking["end_date"], new_end_date)
    if not extended:
        raise HTTPException(status_code=409, detail="Extension dates not available")

    old_end = datetime.fromisoformat(booking["end_date"])
    new_end = datetime.fromisoformat(new_end_date)
    extra_days = max(1, (new_end - old_end).days)
    extension_cost = extra_days * booking["daily_rate"]
    now = datetime.now(timezone.utc).isoformat()

    new_extension = booking.get("extension_amount", 0) + extension_cost
    await db.bookings.update_one(
        {"booking_id": booking_id},
        {"$set": {
            "end_date": new_end_date,
            "total_days": booking["total_days"] + extra_days,
            "extension_amount": new_extension,
            "total_amount": booking["base_amount"] + new_extension,
            "updated_at": now
        }}
    )

    pay_result = await payment_gateway.create_payment(extension_cost, "INR")
    await db.payments.insert_one({
        "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
        "booking_id": booking_id, "user_id": user["user_id"],
        "amount": extension_cost, "currency": "INR", "type": "extension",
        "status": "completed", "payment_method": "mock_gateway",
        "gateway_reference": pay_result.reference, "created_at": now
    })

    return {"message": "Booking extended", "extra_days": extra_days, "extension_cost": extension_cost}
