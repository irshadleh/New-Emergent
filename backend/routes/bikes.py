from fastapi import APIRouter, HTTPException, Request
from database import db
from models import BikeCreate, ShopCreate
from routes.auth import get_current_user
import uuid
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["bikes"])


@router.get("/bikes")
async def list_bikes(
    type: Optional[str] = None,
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    query = {"is_available": True}
    if type:
        query["type"] = type
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
        ]

    price_filter = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        query["daily_rate"] = price_filter

    skip = (page - 1) * limit
    bikes = await db.bikes.find(query, {"_id": 0, "booking_slots": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.bikes.count_documents(query)

    for bike in bikes:
        shop = await db.bike_shops.find_one({"shop_id": bike.get("shop_id")}, {"_id": 0, "name": 1})
        bike["shop_name"] = shop["name"] if shop else ""
        rating_agg = await db.reviews.aggregate([
            {"$match": {"bike_id": bike["bike_id"]}},
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
        ]).to_list(1)
        if rating_agg:
            bike["rating"] = round(rating_agg[0]["avg"], 1)
            bike["total_reviews"] = rating_agg[0]["count"]
        else:
            bike["rating"] = 0
            bike["total_reviews"] = 0

    return {"bikes": bikes, "total": total, "page": page, "limit": limit}


@router.get("/bikes/{bike_id}")
async def get_bike(bike_id: str):
    bike = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0})
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")

    shop = await db.bike_shops.find_one({"shop_id": bike.get("shop_id")}, {"_id": 0})
    bike["shop_name"] = shop["name"] if shop else ""
    bike["shop_details"] = {k: v for k, v in (shop or {}).items() if k != "owner_id"} if shop else {}

    reviews = await db.reviews.find({"bike_id": bike_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for review in reviews:
        reviewer = await db.users.find_one({"user_id": review["reviewer_id"]}, {"_id": 0, "name": 1, "profile_picture": 1})
        review["reviewer_name"] = reviewer["name"] if reviewer else "Anonymous"
        review["reviewer_picture"] = reviewer.get("profile_picture", "") if reviewer else ""
    bike["reviews"] = reviews

    rating_agg = await db.reviews.aggregate([
        {"$match": {"bike_id": bike_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]).to_list(1)
    bike["rating"] = round(rating_agg[0]["avg"], 1) if rating_agg else 0
    bike["total_reviews"] = rating_agg[0]["count"] if rating_agg else 0

    booked_slots = [
        {"start_date": s["start_date"], "end_date": s["end_date"]}
        for s in bike.get("booking_slots", [])
        if s.get("status") in ["confirmed", "active"]
    ]
    bike["booked_dates"] = booked_slots
    bike.pop("booking_slots", None)

    return bike


@router.post("/bikes")
async def create_bike(data: BikeCreate, request: Request):
    user = await get_current_user(request)
    if user["role"] != "shop_owner":
        raise HTTPException(status_code=403, detail="Only shop owners can add bikes")

    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=400, detail="Create a shop first")

    bike_id = f"bike_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    bike_doc = {
        "bike_id": bike_id, "shop_id": shop["shop_id"],
        "name": data.name, "type": data.type, "brand": data.brand,
        "model": data.model, "year": data.year, "engine_cc": data.engine_cc,
        "daily_rate": data.daily_rate,
        "weekly_rate": data.weekly_rate or data.daily_rate * 6,
        "images": data.images, "features": data.features,
        "is_available": True, "location": data.location,
        "description": data.description, "booking_slots": [],
        "created_at": now, "updated_at": now
    }
    await db.bikes.insert_one(bike_doc)

    result = {k: v for k, v in bike_doc.items() if k != "_id"}
    result["shop_name"] = shop["name"]
    result["rating"] = 0
    result["total_reviews"] = 0
    return result


@router.put("/bikes/{bike_id}")
async def update_bike(bike_id: str, request: Request):
    user = await get_current_user(request)
    bike = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0})
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")

    shop = await db.bike_shops.find_one({"shop_id": bike["shop_id"]}, {"_id": 0})
    if not shop or shop["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    body = await request.json()
    update_fields = {}
    for field in ["name", "type", "brand", "model", "year", "engine_cc",
                   "daily_rate", "weekly_rate", "images", "features",
                   "is_available", "location", "description"]:
        if field in body:
            update_fields[field] = body[field]
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.bikes.update_one({"bike_id": bike_id}, {"$set": update_fields})
    updated = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0, "booking_slots": 0})
    updated["shop_name"] = shop["name"]
    return updated


@router.delete("/bikes/{bike_id}")
async def delete_bike(bike_id: str, request: Request):
    user = await get_current_user(request)
    bike = await db.bikes.find_one({"bike_id": bike_id}, {"_id": 0})
    if not bike:
        raise HTTPException(status_code=404, detail="Bike not found")

    shop = await db.bike_shops.find_one({"shop_id": bike["shop_id"]}, {"_id": 0})
    if not shop or shop["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    active = [s for s in bike.get("booking_slots", []) if s["status"] in ["confirmed", "active"]]
    if active:
        raise HTTPException(status_code=400, detail="Cannot delete bike with active bookings")

    await db.bikes.delete_one({"bike_id": bike_id})
    return {"message": "Bike deleted"}


# --- Shop Routes ---

@router.get("/shops")
async def list_shops():
    shops = await db.bike_shops.find({}, {"_id": 0}).to_list(100)
    return {"shops": shops}


@router.get("/shops/{shop_id}")
async def get_shop(shop_id: str):
    shop = await db.bike_shops.find_one({"shop_id": shop_id}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    bikes = await db.bikes.find({"shop_id": shop_id}, {"_id": 0, "booking_slots": 0}).to_list(100)
    shop["bikes"] = bikes
    return shop


@router.post("/shops")
async def create_shop(data: ShopCreate, request: Request):
    user = await get_current_user(request)

    existing = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="You already have a shop")

    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"role": "shop_owner"}}
    )

    shop_id = f"shop_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    shop_doc = {
        "shop_id": shop_id, "owner_id": user["user_id"],
        "name": data.name, "description": data.description,
        "address": data.address, "phone": data.phone,
        "rating": 0, "total_reviews": 0, "is_verified": False,
        "operating_hours": {"open": data.operating_hours_open, "close": data.operating_hours_close},
        "created_at": now
    }
    await db.bike_shops.insert_one(shop_doc)

    result = {k: v for k, v in shop_doc.items() if k != "_id"}
    return result


@router.put("/shops/{shop_id}")
async def update_shop(shop_id: str, request: Request):
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"shop_id": shop_id}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop["owner_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    body = await request.json()
    update_fields = {}
    for field in ["name", "description", "address", "phone", "operating_hours"]:
        if field in body:
            update_fields[field] = body[field]

    await db.bike_shops.update_one({"shop_id": shop_id}, {"$set": update_fields})
    updated = await db.bike_shops.find_one({"shop_id": shop_id}, {"_id": 0})
    return updated


@router.get("/my-shop")
async def get_my_shop(request: Request):
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        return {"shop": None}
    bikes = await db.bikes.find({"shop_id": shop["shop_id"]}, {"_id": 0, "booking_slots": 0}).to_list(100)
    shop["bikes"] = bikes
    return {"shop": shop}
