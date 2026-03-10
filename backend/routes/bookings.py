from fastapi import APIRouter, HTTPException, Request
from database import db
from models import BookingCreate
from routes.auth import get_current_user
from adapters import payment_gateway
import uuid
from datetime import datetime, timezone, timedelta
from pymongo import ReturnDocument
import math
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["bookings"])


def calculate_penalty(end_date_str, actual_return_str, daily_rate):
    """Late return penalty: 2hr grace, then 1.5x daily rate per extra day"""
    end_date = datetime.fromisoformat(end_date_str)
    actual_return = datetime.fromisoformat(actual_return_str)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if actual_return.tzinfo is None:
        actual_return = actual_return.replace(tzinfo=timezone.utc)

    grace_deadline = end_date + timedelta(hours=2)
    if actual_return <= grace_deadline:
        return 0
    extra_hours = (actual_return - end_date).total_seconds() / 3600
    extra_days = math.ceil(extra_hours / 24)
    return extra_days * daily_rate * 1.5


async def create_notification(user_id, notif_type, title, message, data=None):
    notif_doc = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id, "type": notif_type,
        "title": title, "message": message,
        "data": data or {}, "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notif_doc)


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
    daily_rate = bike["daily_rate"]

    if total_days >= 7 and bike.get("weekly_rate"):
        weeks = total_days // 7
        remaining = total_days % 7
        base_amount = (weeks * bike["weekly_rate"]) + (remaining * daily_rate)
    else:
        base_amount = total_days * daily_rate

    booking_id = f"booking_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    # ATOMIC DOUBLE-BOOKING PREVENTION
    result = await db.bikes.find_one_and_update(
        {
            "bike_id": data.bike_id,
            "booking_slots": {
                "$not": {
                    "$elemMatch": {
                        "start_date": {"$lt": data.end_date},
                        "end_date": {"$gt": data.start_date},
                        "status": {"$in": ["confirmed", "active"]}
                    }
                }
            }
        },
        {
            "$push": {
                "booking_slots": {
                    "booking_id": booking_id,
                    "start_date": data.start_date,
                    "end_date": data.end_date,
                    "status": "confirmed"
                }
            }
        },
        return_document=ReturnDocument.AFTER
    )

    if result is None:
        raise HTTPException(
            status_code=409,
            detail="Bike is not available for the selected dates"
        )

    shop = await db.bike_shops.find_one({"shop_id": bike["shop_id"]}, {"_id": 0, "name": 1, "owner_id": 1})

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
        "created_at": now, "updated_at": now
    }
    await db.bookings.insert_one(booking_doc)

    # Mock payment
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

    # Payout ledger
    commission_rate = 0.10
    commission = base_amount * commission_rate
    await db.payout_ledger.insert_one({
        "payout_id": f"payout_{uuid.uuid4().hex[:12]}",
        "shop_id": bike["shop_id"], "booking_id": booking_id,
        "amount": base_amount - commission,
        "commission_rate": commission_rate,
        "commission_amount": commission,
        "status": "pending", "payout_date": None, "created_at": now
    })

    # Notifications
    await create_notification(
        user["user_id"], "booking_confirmed", "Booking Confirmed!",
        f"Your {bike['name']} is booked from {data.start_date[:10]} to {data.end_date[:10]}",
        {"booking_id": booking_id}
    )
    if shop:
        await create_notification(
            shop["owner_id"], "new_booking", "New Booking Received!",
            f"{user['name']} booked {bike['name']} ({data.start_date[:10]} to {data.end_date[:10]})",
            {"booking_id": booking_id}
        )

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
    if new_status not in valid_transitions.get(current, []):
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

    await create_notification(
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
    penalty = calculate_penalty(booking["end_date"], now, booking["daily_rate"])

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
        await create_notification(
            booking["customer_id"], "penalty_applied", "Late Return Penalty",
            f"A penalty of {penalty:.0f} INR has been applied",
            {"booking_id": booking_id, "penalty": penalty}
        )

    await create_notification(
        booking["customer_id"], "booking_completed", "Ride Complete!",
        "Thanks for riding! Don't forget to leave a review.",
        {"booking_id": booking_id}
    )
    return {"message": "Bike returned", "penalty": penalty, "total_amount": update["total_amount"]}


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

    result = await db.bikes.find_one_and_update(
        {
            "bike_id": booking["bike_id"],
            "booking_slots": {
                "$not": {
                    "$elemMatch": {
                        "booking_id": {"$ne": booking_id},
                        "start_date": {"$lt": new_end_date},
                        "end_date": {"$gt": booking["end_date"]},
                        "status": {"$in": ["confirmed", "active"]}
                    }
                }
            }
        },
        {"$set": {"booking_slots.$[elem].end_date": new_end_date}},
        array_filters=[{"elem.booking_id": booking_id}],
        return_document=ReturnDocument.AFTER
    )

    if result is None:
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
