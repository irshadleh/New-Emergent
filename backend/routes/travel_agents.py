"""
Travel Agent Routes — referral management, commission tracking.
"""
from fastapi import APIRouter, HTTPException, Request
from database import db
from routes.auth import get_current_user
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/travel-agent", tags=["travel_agents"])

REFERRAL_COMMISSION_RATE = 0.05  # 5% referral commission


@router.get("/dashboard")
async def agent_dashboard(request: Request):
    """Travel agent dashboard: referral stats, commission, top referrals."""
    user = await get_current_user(request)

    # Count referrals
    total_referrals = await db.bookings.count_documents({"referred_by": user["user_id"]})
    completed_referrals = await db.bookings.count_documents({"referred_by": user["user_id"], "status": "completed"})

    # Commission earned
    commission_pipeline = [
        {"$match": {"referred_by": user["user_id"], "payment_status": "paid"}},
        {"$group": {"_id": None, "total_booking_value": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]
    comm_result = await db.bookings.aggregate(commission_pipeline).to_list(1)
    total_booking_value = comm_result[0]["total_booking_value"] if comm_result else 0
    total_commission = total_booking_value * REFERRAL_COMMISSION_RATE

    # Recent referrals
    recent = await db.bookings.find(
        {"referred_by": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    for r in recent:
        customer = await db.users.find_one({"user_id": r["customer_id"]}, {"_id": 0, "name": 1})
        r["customer_name"] = customer["name"] if customer else ""
        r["commission"] = r.get("total_amount", 0) * REFERRAL_COMMISSION_RATE

    # Referral code
    referral_code = user.get("referral_code", "")
    if not referral_code:
        referral_code = f"REF-{user['user_id'][-8:].upper()}"
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"referral_code": referral_code}}
        )

    return {
        "referral_code": referral_code,
        "stats": {
            "total_referrals": total_referrals,
            "completed_referrals": completed_referrals,
            "total_booking_value": total_booking_value,
            "total_commission": total_commission,
            "commission_rate": f"{REFERRAL_COMMISSION_RATE * 100}%"
        },
        "recent_referrals": recent
    }


@router.post("/generate-link")
async def generate_referral_link(request: Request):
    """Generate a unique referral booking link."""
    user = await get_current_user(request)
    body = await request.json()
    bike_id = body.get("bike_id")

    referral_code = user.get("referral_code", f"REF-{user['user_id'][-8:].upper()}")
    if not user.get("referral_code"):
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"referral_code": referral_code}}
        )

    link = f"/marketplace?ref={referral_code}"
    if bike_id:
        link = f"/bikes/{bike_id}?ref={referral_code}"

    return {"referral_link": link, "referral_code": referral_code}


@router.get("/commission-ledger")
async def commission_ledger(request: Request, page: int = 1, limit: int = 50):
    """Detailed commission ledger for travel agent."""
    user = await get_current_user(request)
    skip = (page - 1) * limit

    pipeline = [
        {"$match": {"referred_by": user["user_id"], "payment_status": "paid"}},
        {"$sort": {"created_at": -1}},
        {"$skip": skip}, {"$limit": limit},
        {"$project": {
            "_id": 0, "booking_id": 1, "bike_name": 1, "shop_name": 1,
            "total_amount": 1, "status": 1, "created_at": 1,
            "commission": {"$multiply": ["$total_amount", REFERRAL_COMMISSION_RATE]}
        }}
    ]
    entries = await db.bookings.aggregate(pipeline).to_list(limit)
    total = await db.bookings.count_documents({"referred_by": user["user_id"], "payment_status": "paid"})

    return {"entries": entries, "total": total, "page": page, "commission_rate": REFERRAL_COMMISSION_RATE}
