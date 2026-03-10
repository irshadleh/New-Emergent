from fastapi import APIRouter, HTTPException, Request
from database import db
from routes.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/shop")
async def shop_analytics(request: Request):
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    shop_id = shop["shop_id"]

    # Total bikes
    total_bikes = await db.bikes.count_documents({"shop_id": shop_id})

    # Booking stats
    total_bookings = await db.bookings.count_documents({"shop_id": shop_id})
    active_bookings = await db.bookings.count_documents({"shop_id": shop_id, "status": {"$in": ["confirmed", "active"]}})
    completed_bookings = await db.bookings.count_documents({"shop_id": shop_id, "status": "completed"})

    # Revenue
    revenue_pipeline = [
        {"$match": {"shop_id": shop_id, "payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]
    revenue_result = await db.bookings.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0

    # Payout summary
    payout_pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {
            "_id": "$status",
            "total": {"$sum": "$amount"},
            "commission": {"$sum": "$commission_amount"}
        }}
    ]
    payout_result = await db.payout_ledger.aggregate(payout_pipeline).to_list(10)
    payouts = {r["_id"]: {"amount": r["total"], "commission": r["commission"]} for r in payout_result}

    # Bike utilization
    bikes = await db.bikes.find({"shop_id": shop_id}, {"_id": 0, "bike_id": 1, "name": 1, "booking_slots": 1}).to_list(100)
    utilization = []
    for bike in bikes:
        slots = bike.get("booking_slots", [])
        active = len([s for s in slots if s["status"] in ["confirmed", "active"]])
        completed = len([s for s in slots if s["status"] == "completed"])
        utilization.append({
            "bike_id": bike["bike_id"],
            "name": bike["name"],
            "active_bookings": active,
            "completed_bookings": completed,
            "total_bookings": active + completed
        })

    # Monthly revenue (last 6 months)
    monthly_pipeline = [
        {"$match": {"shop_id": shop_id, "payment_status": "paid"}},
        {"$addFields": {"date_parsed": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$date_parsed"}},
            "revenue": {"$sum": "$total_amount"},
            "bookings": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 6}
    ]
    monthly = await db.bookings.aggregate(monthly_pipeline).to_list(6)

    # Reviews
    rating_pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    rating_result = await db.reviews.aggregate(rating_pipeline).to_list(1)

    return {
        "shop": {"name": shop["name"], "shop_id": shop_id},
        "stats": {
            "total_bikes": total_bikes,
            "total_bookings": total_bookings,
            "active_bookings": active_bookings,
            "completed_bookings": completed_bookings,
            "total_revenue": total_revenue,
            "average_rating": round(rating_result[0]["avg"], 1) if rating_result else 0,
            "total_reviews": rating_result[0]["count"] if rating_result else 0
        },
        "payouts": payouts,
        "bike_utilization": utilization,
        "monthly_revenue": [{"month": m["_id"], "revenue": m["revenue"], "bookings": m["bookings"]} for m in monthly]
    }


@router.get("/analytics/overview")
async def overview_analytics(request: Request):
    """Admin overview analytics"""
    user = await get_current_user(request)

    total_users = await db.users.count_documents({})
    total_shops = await db.bike_shops.count_documents({})
    total_bikes = await db.bikes.count_documents({})
    total_bookings = await db.bookings.count_documents({})

    revenue_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
    ]
    revenue_result = await db.bookings.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0

    return {
        "total_users": total_users,
        "total_shops": total_shops,
        "total_bikes": total_bikes,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue
    }


@router.get("/payments/history")
async def payment_history(request: Request):
    user = await get_current_user(request)
    payments = await db.payments.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"payments": payments}
