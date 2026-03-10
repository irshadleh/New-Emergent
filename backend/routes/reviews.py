from fastapi import APIRouter, HTTPException, Request
from database import db
from models import ReviewCreate
from routes.auth import get_current_user
from services.rating_engine import create_bike_review, create_customer_rating, get_customer_rating, get_rating_flags
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["reviews"])


@router.post("/reviews")
async def create_review(data: ReviewCreate, request: Request):
    user = await get_current_user(request)
    result = await create_bike_review(user["user_id"], data.booking_id, data.rating, data.comment)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/reviews/customer")
async def rate_customer(request: Request):
    """Shop owner rates a customer (bidirectional rating)."""
    user = await get_current_user(request)
    body = await request.json()
    booking_id = body.get("booking_id")
    rating = body.get("rating")
    comment = body.get("comment", "")

    if not booking_id or not rating:
        raise HTTPException(status_code=400, detail="booking_id and rating required")

    result = await create_customer_rating(user["user_id"], booking_id, rating, comment)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/reviews/customer/{customer_id}")
async def get_customer_reviews(customer_id: str):
    """Get aggregated customer rating."""
    return await get_customer_rating(customer_id)


@router.get("/reviews/bike/{bike_id}")
async def get_bike_reviews(bike_id: str):
    reviews = await db.reviews.find({"bike_id": bike_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for review in reviews:
        reviewer = await db.users.find_one(
            {"user_id": review["reviewer_id"]}, {"_id": 0, "name": 1, "profile_picture": 1}
        )
        review["reviewer_name"] = reviewer["name"] if reviewer else "Anonymous"
        review["reviewer_picture"] = reviewer.get("profile_picture", "") if reviewer else ""
    return {"reviews": reviews}


@router.get("/reviews/shop/{shop_id}")
async def get_shop_reviews(shop_id: str):
    reviews = await db.reviews.find({"shop_id": shop_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for review in reviews:
        reviewer = await db.users.find_one(
            {"user_id": review["reviewer_id"]}, {"_id": 0, "name": 1, "profile_picture": 1}
        )
        review["reviewer_name"] = reviewer["name"] if reviewer else "Anonymous"
        review["reviewer_picture"] = reviewer.get("profile_picture", "") if reviewer else ""
    return {"reviews": reviews}


@router.get("/reviews/flags")
async def get_flags(request: Request, shop_id: str = None):
    """Get flagged low ratings for admin/owner review."""
    user = await get_current_user(request)
    if user["role"] == "shop_owner":
        shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
        shop_id = shop["shop_id"] if shop else None
    flags = await get_rating_flags(shop_id)
    return {"flags": flags}
