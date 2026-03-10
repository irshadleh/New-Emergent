"""
Rating Engine — bidirectional rating system.

Customer → Bike/Shop (existing review system)
Shop Owner → Customer (new: reliability rating)

Aggregation and flag system for low ratings.
"""
from database import db
from services.notification_engine import dispatch_notification
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


async def create_bike_review(reviewer_id: str, booking_id: str, rating: int, comment: str) -> dict:
    """Customer reviews a bike after a completed booking."""
    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        return {"error": "Booking not found"}
    if booking["customer_id"] != reviewer_id:
        return {"error": "Not authorized"}
    if booking["status"] != "completed":
        return {"error": "Can only review completed bookings"}

    existing = await db.reviews.find_one(
        {"booking_id": booking_id, "reviewer_id": reviewer_id}, {"_id": 0}
    )
    if existing:
        return {"error": "Already reviewed"}

    if not 1 <= rating <= 5:
        return {"error": "Rating must be 1-5"}

    review_id = f"rev_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    review_doc = {
        "review_id": review_id, "booking_id": booking_id,
        "bike_id": booking["bike_id"], "shop_id": booking["shop_id"],
        "reviewer_id": reviewer_id, "rating": rating,
        "comment": comment, "type": "bike_review",
        "created_at": now
    }
    await db.reviews.insert_one(review_doc)

    # Update aggregated ratings
    await _update_bike_rating(booking["bike_id"])
    await _update_shop_rating(booking["shop_id"])

    # Notify shop owner
    shop = await db.bike_shops.find_one({"shop_id": booking["shop_id"]}, {"_id": 0, "owner_id": 1})
    if shop:
        reviewer = await db.users.find_one({"user_id": reviewer_id}, {"_id": 0, "name": 1})
        await dispatch_notification(shop["owner_id"], "review_received", {
            "bike_name": booking.get("bike_name", ""),
            "rating": str(rating),
            "comment": comment[:80],
            "reviewer_name": reviewer["name"] if reviewer else ""
        }, {"review_id": review_id, "bike_id": booking["bike_id"]})

    # Flag low rating for attention
    if rating <= 2:
        await db.rating_flags.insert_one({
            "flag_id": f"flag_{uuid.uuid4().hex[:8]}",
            "review_id": review_id, "bike_id": booking["bike_id"],
            "shop_id": booking["shop_id"], "rating": rating,
            "reason": "Low rating requires attention",
            "resolved": False, "created_at": now
        })
        logger.warning(f"[RATING FLAG] Low rating ({rating}) for bike {booking['bike_id']}")

    result = {k: v for k, v in review_doc.items() if k != "_id"}
    return result


async def create_customer_rating(shop_owner_id: str, booking_id: str, rating: int, comment: str) -> dict:
    """Shop owner rates a customer (reliability, condition of bike return, etc.)."""
    booking = await db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        return {"error": "Booking not found"}

    shop = await db.bike_shops.find_one({"shop_id": booking["shop_id"]}, {"_id": 0})
    if not shop or shop["owner_id"] != shop_owner_id:
        return {"error": "Not authorized"}

    if booking["status"] != "completed":
        return {"error": "Can only rate completed bookings"}

    existing = await db.customer_ratings.find_one(
        {"booking_id": booking_id, "rated_by": shop_owner_id}, {"_id": 0}
    )
    if existing:
        return {"error": "Already rated this customer"}

    if not 1 <= rating <= 5:
        return {"error": "Rating must be 1-5"}

    rating_id = f"crat_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    rating_doc = {
        "rating_id": rating_id, "booking_id": booking_id,
        "customer_id": booking["customer_id"],
        "shop_id": booking["shop_id"],
        "rated_by": shop_owner_id, "rating": rating,
        "comment": comment, "type": "customer_rating",
        "created_at": now
    }
    await db.customer_ratings.insert_one(rating_doc)

    # Update customer's aggregate rating
    await _update_customer_rating(booking["customer_id"])

    # Notify customer
    await dispatch_notification(booking["customer_id"], "customer_rating", {}, {
        "rating": rating, "rating_id": rating_id
    })

    result = {k: v for k, v in rating_doc.items() if k != "_id"}
    logger.info(f"[CUSTOMER RATING] Customer {booking['customer_id']} rated {rating}/5 by shop {booking['shop_id']}")
    return result


async def get_customer_rating(customer_id: str) -> dict:
    """Get aggregated customer rating."""
    pipeline = [
        {"$match": {"customer_id": customer_id}},
        {"$group": {
            "_id": None, "avg": {"$avg": "$rating"},
            "count": {"$sum": 1},
            "ratings": {"$push": {"rating": "$rating", "comment": "$comment", "created_at": "$created_at"}}
        }}
    ]
    result = await db.customer_ratings.aggregate(pipeline).to_list(1)

    if not result:
        return {"customer_id": customer_id, "avg_rating": 0, "total_ratings": 0, "ratings": []}

    return {
        "customer_id": customer_id,
        "avg_rating": round(result[0]["avg"], 1),
        "total_ratings": result[0]["count"],
        "ratings": sorted(result[0]["ratings"], key=lambda x: x.get("created_at", ""), reverse=True)[:20]
    }


async def _update_bike_rating(bike_id: str):
    """Recalculate and store aggregated bike rating."""
    pipeline = [
        {"$match": {"bike_id": bike_id, "type": "bike_review"}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    result = await db.reviews.aggregate(pipeline).to_list(1)
    if result:
        await db.bikes.update_one(
            {"bike_id": bike_id},
            {"$set": {"cached_rating": round(result[0]["avg"], 1), "cached_review_count": result[0]["count"]}}
        )


async def _update_shop_rating(shop_id: str):
    """Recalculate and store aggregated shop rating."""
    pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    result = await db.reviews.aggregate(pipeline).to_list(1)
    if result:
        await db.bike_shops.update_one(
            {"shop_id": shop_id},
            {"$set": {"rating": round(result[0]["avg"], 1), "total_reviews": result[0]["count"]}}
        )


async def _update_customer_rating(customer_id: str):
    """Recalculate and store aggregated customer rating."""
    pipeline = [
        {"$match": {"customer_id": customer_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    result = await db.customer_ratings.aggregate(pipeline).to_list(1)
    if result:
        await db.users.update_one(
            {"user_id": customer_id},
            {"$set": {"customer_rating": round(result[0]["avg"], 1), "customer_rating_count": result[0]["count"]}}
        )


async def get_rating_flags(shop_id: str = None, resolved: bool = False) -> list:
    """Get flagged low ratings for review."""
    query = {"resolved": resolved}
    if shop_id:
        query["shop_id"] = shop_id
    flags = await db.rating_flags.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return flags
