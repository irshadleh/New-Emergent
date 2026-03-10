"""
Admin Routes — platform management, user oversight, payout approval, KYC review.
All routes require admin role.
"""
from fastapi import APIRouter, HTTPException, Request
from database import db
from routes.auth import get_current_user
from services.analytics_engine import get_platform_analytics
from services.payout_engine import process_settlement
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(request: Request):
    """Guard: require admin role."""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/dashboard")
async def admin_dashboard(request: Request):
    """Full platform dashboard with analytics."""
    await require_admin(request)
    analytics = await get_platform_analytics()

    # Additional admin-specific metrics
    pending_kyc = await db.users.count_documents({"kyc_status": "pending"})
    pending_payouts = await db.payout_ledger.count_documents({"status": "pending"})
    total_settlements = await db.settlements.count_documents({})

    # Recent bookings
    recent_bookings = await db.bookings.find(
        {}, {"_id": 0, "booking_id": 1, "bike_name": 1, "customer_id": 1,
             "total_amount": 1, "status": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)

    for b in recent_bookings:
        customer = await db.users.find_one(
            {"user_id": b["customer_id"]}, {"_id": 0, "name": 1, "email": 1}
        )
        b["customer_name"] = customer["name"] if customer else ""
        b["customer_email"] = customer.get("email", "") if customer else ""

    analytics["admin_metrics"] = {
        "pending_kyc": pending_kyc,
        "pending_payouts": pending_payouts,
        "total_settlements": total_settlements,
    }
    analytics["recent_bookings"] = recent_bookings
    return analytics


@router.get("/users")
async def list_users(request: Request, role: str = None, kyc_status: str = None,
                     search: str = None, page: int = 1, limit: int = 20):
    """List all users with filters."""
    await require_admin(request)

    query = {}
    if role:
        query["role"] = role
    if kyc_status:
        query["kyc_status"] = kyc_status
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]

    skip = (page - 1) * limit
    total = await db.users.count_documents(query)
    users = await db.users.find(
        query, {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    return {"users": users, "total": total, "page": page, "limit": limit}


@router.put("/users/{user_id}")
async def update_user(user_id: str, request: Request):
    """Admin update user — role, status, suspension."""
    await require_admin(request)
    body = await request.json()
    now = datetime.now(timezone.utc).isoformat()

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update = {"updated_at": now}
    if "role" in body:
        allowed_roles = ["customer", "shop_owner", "travel_agent", "admin"]
        if body["role"] not in allowed_roles:
            raise HTTPException(status_code=400, detail="Invalid role")
        update["role"] = body["role"]

    if "is_suspended" in body:
        update["is_suspended"] = body["is_suspended"]

    if "kyc_status" in body:
        allowed_statuses = ["pending", "approved", "rejected"]
        if body["kyc_status"] not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Invalid KYC status")
        update["kyc_status"] = body["kyc_status"]

    await db.users.update_one({"user_id": user_id}, {"$set": update})
    updated = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return updated


@router.get("/payouts")
async def admin_payouts(request: Request, status: str = None, page: int = 1, limit: int = 20):
    """List all payouts across all shops."""
    await require_admin(request)

    query = {}
    if status:
        query["status"] = status

    skip = (page - 1) * limit
    total = await db.payout_ledger.count_documents(query)
    entries = await db.payout_ledger.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    for entry in entries:
        shop = await db.bike_shops.find_one(
            {"shop_id": entry["shop_id"]}, {"_id": 0, "name": 1}
        )
        entry["shop_name"] = shop["name"] if shop else ""
        booking = await db.bookings.find_one(
            {"booking_id": entry["booking_id"]},
            {"_id": 0, "bike_name": 1, "customer_id": 1}
        )
        if booking:
            entry["bike_name"] = booking.get("bike_name", "")
            customer = await db.users.find_one(
                {"user_id": booking["customer_id"]}, {"_id": 0, "name": 1}
            )
            entry["customer_name"] = customer["name"] if customer else ""

    # Summary stats
    summary_pipeline = [
        {"$group": {
            "_id": "$status",
            "total_amount": {"$sum": "$amount"},
            "total_commission": {"$sum": "$commission_amount"},
            "count": {"$sum": 1}
        }}
    ]
    summary = {r["_id"]: {"amount": r["total_amount"], "commission": r["total_commission"], "count": r["count"]}
               for r in await db.payout_ledger.aggregate(summary_pipeline).to_list(10)}

    return {
        "entries": entries, "total": total, "page": page, "limit": limit,
        "summary": summary
    }


@router.post("/payouts/{shop_id}/settle")
async def admin_settle_shop(shop_id: str, request: Request):
    """Admin triggers settlement for a specific shop."""
    await require_admin(request)
    shop = await db.bike_shops.find_one({"shop_id": shop_id}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    result = await process_settlement(shop_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/kyc")
async def list_kyc(request: Request, status: str = None, page: int = 1, limit: int = 20):
    """List users with KYC review pending."""
    await require_admin(request)

    query = {}
    if status:
        query["kyc_status"] = status
    else:
        query["kyc_status"] = {"$in": ["pending", "approved", "rejected"]}

    skip = (page - 1) * limit
    total = await db.users.count_documents(query)
    users = await db.users.find(
        query, {"_id": 0, "password_hash": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    return {"users": users, "total": total, "page": page, "limit": limit}


@router.post("/kyc/{user_id}/review")
async def review_kyc(user_id: str, request: Request):
    """Approve or reject a user's KYC submission."""
    admin = await require_admin(request)
    body = await request.json()
    new_status = body.get("status")
    notes = body.get("notes", "")

    if new_status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "kyc_status": new_status,
            "kyc_reviewed_by": admin["user_id"],
            "kyc_reviewed_at": now,
            "kyc_notes": notes,
            "updated_at": now
        }}
    )

    return {"message": f"KYC {new_status}", "user_id": user_id, "status": new_status}
