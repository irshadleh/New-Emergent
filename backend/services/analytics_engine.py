"""
Analytics Engine — bike performance, revenue tracking, utilization.

Generates analytics for:
  - Individual bike performance (utilization, revenue, ratings)
  - Shop-level revenue and booking trends
  - Platform-wide metrics for admin dashboard
  - Customer segmentation and booking patterns
"""
from database import db
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


async def get_bike_performance(bike_id: str) -> dict:
    """Detailed performance analytics for a single bike."""
    bike = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0})
    if not bike:
        return {"error": "Bike not found"}

    # Booking stats
    total_bookings = await db.bookings.count_documents({"bike_id": bike_id})
    completed = await db.bookings.count_documents({"bike_id": bike_id, "status": "completed"})
    cancelled = await db.bookings.count_documents({"bike_id": bike_id, "status": "cancelled"})
    active = await db.bookings.count_documents({"bike_id": bike_id, "status": {"$in": ["confirmed", "active"]}})

    # Revenue
    rev_pipeline = [
        {"$match": {"bike_id": bike_id, "payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}, "avg": {"$avg": "$total_amount"}}}
    ]
    rev = await db.bookings.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev[0]["total"] if rev else 0
    avg_booking_value = round(rev[0]["avg"], 2) if rev else 0

    # Utilization: days booked / days since listed
    created = datetime.fromisoformat(bike.get("created_at", datetime.now(timezone.utc).isoformat()))
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    days_listed = max(1, (datetime.now(timezone.utc) - created).days)

    days_booked_pipeline = [
        {"$match": {"bike_id": bike_id, "status": {"$in": ["completed", "active", "confirmed"]}}},
        {"$group": {"_id": None, "total_days": {"$sum": "$total_days"}}}
    ]
    days_result = await db.bookings.aggregate(days_booked_pipeline).to_list(1)
    total_booked_days = days_result[0]["total_days"] if days_result else 0
    utilization_rate = round(min(100, (total_booked_days / days_listed) * 100), 1)

    # Rating
    rating_pipeline = [
        {"$match": {"bike_id": bike_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1},
                     "dist": {"$push": "$rating"}}}
    ]
    rating_result = await db.reviews.aggregate(rating_pipeline).to_list(1)
    avg_rating = round(rating_result[0]["avg"], 1) if rating_result else 0
    review_count = rating_result[0]["count"] if rating_result else 0
    rating_distribution = {}
    if rating_result:
        for r in rating_result[0].get("dist", []):
            rating_distribution[str(r)] = rating_distribution.get(str(r), 0) + 1

    # Penalties
    penalty_pipeline = [
        {"$match": {"bike_id": bike_id, "penalty_amount": {"$gt": 0}}},
        {"$group": {"_id": None, "total": {"$sum": "$penalty_amount"}, "count": {"$sum": 1}}}
    ]
    penalty_result = await db.bookings.aggregate(penalty_pipeline).to_list(1)
    total_penalties = penalty_result[0]["total"] if penalty_result else 0
    penalty_count = penalty_result[0]["count"] if penalty_result else 0

    # Monthly revenue (last 6 months)
    monthly_pipeline = [
        {"$match": {"bike_id": bike_id, "payment_status": "paid"}},
        {"$addFields": {"date_parsed": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$date_parsed"}},
            "revenue": {"$sum": "$total_amount"}, "bookings": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}, {"$limit": 6}
    ]
    monthly = await db.bookings.aggregate(monthly_pipeline).to_list(6)

    return {
        "bike_id": bike_id,
        "name": bike.get("name", ""),
        "type": bike.get("type", ""),
        "daily_rate": bike.get("daily_rate", 0),
        "stats": {
            "total_bookings": total_bookings,
            "completed_bookings": completed,
            "cancelled_bookings": cancelled,
            "active_bookings": active,
            "total_revenue": total_revenue,
            "avg_booking_value": avg_booking_value,
            "total_booked_days": total_booked_days,
            "days_listed": days_listed,
            "utilization_rate": utilization_rate,
            "avg_rating": avg_rating,
            "review_count": review_count,
            "rating_distribution": rating_distribution,
            "total_penalties": total_penalties,
            "penalty_incidents": penalty_count
        },
        "monthly_revenue": [{"month": m["_id"], "revenue": m["revenue"], "bookings": m["bookings"]} for m in monthly]
    }


async def get_shop_analytics(shop_id: str) -> dict:
    """Comprehensive shop-level analytics."""
    shop = await db.bike_shops.find_one({"shop_id": shop_id}, {"_id": 0})
    if not shop:
        return {"error": "Shop not found"}

    total_bikes = await db.bikes.count_documents({"shop_id": shop_id})
    total_bookings = await db.bookings.count_documents({"shop_id": shop_id})
    active_bookings = await db.bookings.count_documents({"shop_id": shop_id, "status": {"$in": ["confirmed", "active"]}})
    completed_bookings = await db.bookings.count_documents({"shop_id": shop_id, "status": "completed"})
    overdue_bookings = await db.bookings.count_documents({"shop_id": shop_id, "status": "overdue"})

    # Revenue
    rev_pipeline = [
        {"$match": {"shop_id": shop_id, "payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]
    rev = await db.bookings.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev[0]["total"] if rev else 0

    # Payout summary
    payout_pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {"_id": "$status", "total": {"$sum": "$amount"}, "commission": {"$sum": "$commission_amount"}}}
    ]
    payouts = {r["_id"]: {"amount": r["total"], "commission": r["commission"]} for r in await db.payout_ledger.aggregate(payout_pipeline).to_list(10)}

    # Bike utilization
    bikes = await db.bikes.find({"shop_id": shop_id}, {"_id": 0, "bike_id": 1, "name": 1, "booking_slots": 1, "daily_rate": 1}).to_list(100)
    utilization = []
    for bike in bikes:
        slots = bike.get("booking_slots", [])
        active_count = len([s for s in slots if s["status"] in ["confirmed", "active"]])
        completed_count = len([s for s in slots if s["status"] == "completed"])
        utilization.append({
            "bike_id": bike["bike_id"], "name": bike["name"],
            "daily_rate": bike.get("daily_rate", 0),
            "active_bookings": active_count, "completed_bookings": completed_count,
            "total_bookings": active_count + completed_count
        })

    # Monthly revenue
    monthly_pipeline = [
        {"$match": {"shop_id": shop_id, "payment_status": "paid"}},
        {"$addFields": {"date_parsed": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$date_parsed"}},
            "revenue": {"$sum": "$total_amount"}, "bookings": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}, {"$limit": 12}
    ]
    monthly = await db.bookings.aggregate(monthly_pipeline).to_list(12)

    # Reviews
    rating_pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    rating_result = await db.reviews.aggregate(rating_pipeline).to_list(1)

    # Top performing bike
    top_bike_pipeline = [
        {"$match": {"shop_id": shop_id, "payment_status": "paid"}},
        {"$group": {"_id": "$bike_id", "revenue": {"$sum": "$total_amount"}, "bookings": {"$sum": 1}}},
        {"$sort": {"revenue": -1}}, {"$limit": 1}
    ]
    top_bike = await db.bookings.aggregate(top_bike_pipeline).to_list(1)
    top_bike_info = None
    if top_bike:
        bike_doc = await db.bikes.find_one({"bike_id": top_bike[0]["_id"]}, {"_id": 0, "name": 1})
        top_bike_info = {
            "bike_id": top_bike[0]["_id"],
            "name": bike_doc["name"] if bike_doc else "",
            "revenue": top_bike[0]["revenue"],
            "bookings": top_bike[0]["bookings"]
        }

    return {
        "shop": {"name": shop["name"], "shop_id": shop_id},
        "stats": {
            "total_bikes": total_bikes,
            "total_bookings": total_bookings,
            "active_bookings": active_bookings,
            "completed_bookings": completed_bookings,
            "overdue_bookings": overdue_bookings,
            "total_revenue": total_revenue,
            "average_rating": round(rating_result[0]["avg"], 1) if rating_result else 0,
            "total_reviews": rating_result[0]["count"] if rating_result else 0
        },
        "payouts": payouts,
        "bike_utilization": sorted(utilization, key=lambda x: x["total_bookings"], reverse=True),
        "monthly_revenue": [{"month": m["_id"], "revenue": m["revenue"], "bookings": m["bookings"]} for m in monthly],
        "top_performing_bike": top_bike_info
    }


async def get_platform_analytics() -> dict:
    """Platform-wide analytics for admin dashboard. Designed for 50K+ user scale."""
    total_users = await db.users.count_documents({})
    total_shops = await db.bike_shops.count_documents({})
    total_bikes = await db.bikes.count_documents({})
    total_bookings = await db.bookings.count_documents({})

    # User distribution by role
    role_pipeline = [
        {"$group": {"_id": "$role", "count": {"$sum": 1}}}
    ]
    roles = {r["_id"]: r["count"] for r in await db.users.aggregate(role_pipeline).to_list(10)}

    # Booking status distribution
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    statuses = {s["_id"]: s["count"] for s in await db.bookings.aggregate(status_pipeline).to_list(10)}

    # Revenue
    rev_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]
    rev = await db.bookings.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev[0]["total"] if rev else 0

    # Commission earned
    commission_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$commission_amount"}}}
    ]
    commission = await db.payout_ledger.aggregate(commission_pipeline).to_list(1)
    total_commission = commission[0]["total"] if commission else 0

    # Monthly trends
    monthly_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$addFields": {"date_parsed": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$date_parsed"}},
            "revenue": {"$sum": "$total_amount"},
            "bookings": {"$sum": 1},
            "penalties": {"$sum": "$penalty_amount"}
        }},
        {"$sort": {"_id": 1}}, {"$limit": 12}
    ]
    monthly = await db.bookings.aggregate(monthly_pipeline).to_list(12)

    # Top shops by revenue
    top_shops_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": "$shop_id", "revenue": {"$sum": "$total_amount"}, "bookings": {"$sum": 1}}},
        {"$sort": {"revenue": -1}}, {"$limit": 10}
    ]
    top_shops_raw = await db.bookings.aggregate(top_shops_pipeline).to_list(10)
    top_shops = []
    for s in top_shops_raw:
        shop = await db.bike_shops.find_one({"shop_id": s["_id"]}, {"_id": 0, "name": 1})
        top_shops.append({
            "shop_id": s["_id"], "name": shop["name"] if shop else "",
            "revenue": s["revenue"], "bookings": s["bookings"]
        })

    # Popular bike types
    type_pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$lookup": {"from": "bikes", "localField": "bike_id", "foreignField": "bike_id", "as": "bike_info"}},
        {"$unwind": {"path": "$bike_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": "$bike_info.type", "count": {"$sum": 1}, "revenue": {"$sum": "$total_amount"}}},
        {"$sort": {"count": -1}}
    ]
    popular_types = await db.bookings.aggregate(type_pipeline).to_list(10)

    return {
        "overview": {
            "total_users": total_users,
            "total_shops": total_shops,
            "total_bikes": total_bikes,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "total_commission": total_commission
        },
        "user_distribution": roles,
        "booking_statuses": statuses,
        "monthly_trends": [{"month": m["_id"], "revenue": m["revenue"], "bookings": m["bookings"], "penalties": m["penalties"]} for m in monthly],
        "top_shops": top_shops,
        "popular_bike_types": [{"type": t["_id"], "bookings": t["count"], "revenue": t["revenue"]} for t in popular_types if t["_id"]]
    }
