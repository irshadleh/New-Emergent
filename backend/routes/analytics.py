"""
Analytics Routes — bike performance, shop analytics, platform overview.
"""
from fastapi import APIRouter, HTTPException, Request
from database import db
from routes.auth import get_current_user
from services.analytics_engine import get_bike_performance, get_shop_analytics, get_platform_analytics
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/shop")
async def shop_analytics(request: Request):
    """Comprehensive shop analytics for shop owner."""
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return await get_shop_analytics(shop["shop_id"])


@router.get("/analytics/bike/{bike_id}")
async def bike_analytics(bike_id: str, request: Request):
    """Detailed performance analytics for a single bike."""
    user = await get_current_user(request)
    result = await get_bike_performance(bike_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/analytics/platform")
async def platform_analytics(request: Request):
    """Platform-wide analytics for admin dashboard."""
    user = await get_current_user(request)
    return await get_platform_analytics()


@router.get("/analytics/overview")
async def overview_analytics(request: Request):
    """Quick overview stats."""
    user = await get_current_user(request)
    total_users = await db.users.count_documents({})
    total_shops = await db.bike_shops.count_documents({})
    total_bikes = await db.bikes.count_documents({})
    total_bookings = await db.bookings.count_documents({})

    rev_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]
    rev = await db.bookings.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev[0]["total"] if rev else 0

    return {
        "total_users": total_users, "total_shops": total_shops,
        "total_bikes": total_bikes, "total_bookings": total_bookings,
        "total_revenue": total_revenue
    }


@router.get("/payments/history")
async def payment_history(request: Request):
    user = await get_current_user(request)
    payments = await db.payments.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"payments": payments}
