from fastapi import APIRouter, HTTPException, Request
from database import db
from models import ReviewCreate
from routes.auth import get_current_user
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["reviews"])


@router.post("/reviews")
async def create_review(data: ReviewCreate, request: Request):
    user = await get_current_user(request)

    booking = await db.bookings.find_one({"booking_id": data.booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking["customer_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if booking["status"] != "completed":
        raise HTTPException(status_code=400, detail="Can only review completed bookings")

    existing = await db.reviews.find_one(
        {"booking_id": data.booking_id, "reviewer_id": user["user_id"]}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already reviewed this booking")

    if not 1 <= data.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    review_id = f"rev_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    review_doc = {
        "review_id": review_id, "booking_id": data.booking_id,
        "bike_id": booking["bike_id"], "shop_id": booking["shop_id"],
        "reviewer_id": user["user_id"], "rating": data.rating,
        "comment": data.comment, "created_at": now
    }
    await db.reviews.insert_one(review_doc)

    result = {k: v for k, v in review_doc.items() if k != "_id"}
    result["reviewer_name"] = user["name"]
    return result


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
