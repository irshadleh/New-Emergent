from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from database import db, client
from routes.auth import router as auth_router
from routes.bikes import router as bikes_router
from routes.bookings import router as bookings_router
from routes.reviews import router as reviews_router
from routes.notifications import router as notifications_router
from routes.analytics import router as analytics_router
from routes.payouts import router as payouts_router
from routes.travel_agents import router as travel_agent_router
from routes.admin import router as admin_router
from services.booking_engine import scan_overdue_bookings
from services.notification_engine import scan_and_send_reminders
import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone

app = FastAPI(title="Ladakh Moto Market API", version="2.0.0")

# ─── Routers ────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(bikes_router)
app.include_router(bookings_router)
app.include_router(reviews_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(payouts_router)
app.include_router(travel_agent_router)
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ─── Background Tasks ──────────────────────────────────────
_background_task = None

async def background_scheduler():
    """Periodic background tasks: overdue scan + notification reminders."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            overdue_count = await scan_overdue_bookings()
            reminder_counts = await scan_and_send_reminders()
            if overdue_count or reminder_counts.get("pickup_24h") or reminder_counts.get("return_4h"):
                logger.info(f"[BG] Overdue: {overdue_count}, Reminders: {reminder_counts}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[BG] Background task error: {e}")
            await asyncio.sleep(60)


# ─── Seed Data ──────────────────────────────────────────────
SEED_BIKES = [
    {
        "name": "Royal Enfield Himalayan 450", "type": "adventure",
        "brand": "Royal Enfield", "model": "Himalayan 450",
        "year": 2024, "engine_cc": 450, "daily_rate": 1500, "weekly_rate": 9000,
        "images": [
            "https://images.unsplash.com/photo-1689243046860-b3eebddba82f?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["ABS", "GPS Mount", "Panniers", "Helmet Included", "Phone Charger"],
        "location": "Leh Main Market",
        "description": "The ultimate adventure machine for Ladakh. Fuel-injected 450cc engine, perfect for Khardung La and Pangong routes."
    },
    {
        "name": "Royal Enfield Classic 350", "type": "cruiser",
        "brand": "Royal Enfield", "model": "Classic 350",
        "year": 2024, "engine_cc": 350, "daily_rate": 1200, "weekly_rate": 7200,
        "images": [
            "https://images.unsplash.com/photo-1709874859086-b50e500f4136?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["ABS", "Helmet Included", "Saddle Bags"],
        "location": "Leh Main Market",
        "description": "Iconic retro cruiser. Smooth ride for highway touring between Leh and Manali."
    },
    {
        "name": "KTM Adventure 390", "type": "adventure",
        "brand": "KTM", "model": "Adventure 390",
        "year": 2024, "engine_cc": 390, "daily_rate": 1800, "weekly_rate": 10800,
        "images": [
            "https://images.unsplash.com/photo-1449426468159-d96dbf08f19f?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1558980664-769d59546b3d?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["ABS", "Ride Modes", "GPS Mount", "Panniers", "Helmet Included"],
        "location": "Leh Main Market",
        "description": "Lightweight and powerful adventure bike. Quick-shifter, ride modes, and suspension travel for off-road trails."
    },
    {
        "name": "Royal Enfield Bullet 350", "type": "cruiser",
        "brand": "Royal Enfield", "model": "Bullet 350",
        "year": 2023, "engine_cc": 350, "daily_rate": 1000, "weekly_rate": 6000,
        "images": [
            "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["Helmet Included", "Tool Kit"],
        "location": "Leh Old Town",
        "description": "The legendary thump-thump of a Bullet through the mountains. Budget-friendly classic."
    },
    {
        "name": "Honda CB200X", "type": "adventure",
        "brand": "Honda", "model": "CB200X",
        "year": 2024, "engine_cc": 200, "daily_rate": 800, "weekly_rate": 4800,
        "images": [
            "https://images.unsplash.com/photo-1449426468159-d96dbf08f19f?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1558980664-769d59546b3d?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["ABS", "LED Lights", "Helmet Included"],
        "location": "Nubra Valley",
        "description": "Light and fuel-efficient. Ideal for beginners and short Ladakh circuits."
    },
    {
        "name": "Royal Enfield Meteor 350", "type": "cruiser",
        "brand": "Royal Enfield", "model": "Meteor 350",
        "year": 2024, "engine_cc": 350, "daily_rate": 1100, "weekly_rate": 6600,
        "images": [
            "https://images.unsplash.com/photo-1709874859086-b50e500f4136?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["Tripper Navigation", "ABS", "Helmet Included", "Windshield"],
        "location": "Nubra Valley",
        "description": "Built-in turn-by-turn navigation via Tripper. Comfortable for long highway rides."
    },
    {
        "name": "Bajaj Dominar 400", "type": "sport",
        "brand": "Bajaj", "model": "Dominar 400",
        "year": 2024, "engine_cc": 400, "daily_rate": 1300, "weekly_rate": 7800,
        "images": [
            "https://images.unsplash.com/photo-1558980664-769d59546b3d?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1449426468159-d96dbf08f19f?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["ABS", "Slipper Clutch", "Helmet Included"],
        "location": "Leh Main Market",
        "description": "Sporty tourer with a punchy engine. Excellent for highway blasts to Pangong Lake."
    },
    {
        "name": "Hero Xpulse 200 4V", "type": "adventure",
        "brand": "Hero", "model": "Xpulse 200 4V",
        "year": 2024, "engine_cc": 200, "daily_rate": 700, "weekly_rate": 4200,
        "images": [
            "https://images.unsplash.com/photo-1449426468159-d96dbf08f19f?q=80&w=800&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?q=80&w=800&auto=format&fit=crop"
        ],
        "features": ["ABS", "Rally Kit Ready", "Helmet Included"],
        "location": "Pangong Road",
        "description": "Lightweight off-road capable dual-sport. Rally kit available. Best for dirt trails around Ladakh."
    }
]


async def seed_database():
    """Seed database with sample data if empty."""
    bike_count = await db.bikes.count_documents({})
    if bike_count > 0:
        logger.info("Database already seeded")
        return

    logger.info("Seeding database with Ladakh bike shops...")
    now = datetime.now(timezone.utc).isoformat()

    shops = [
        {
            "shop_id": f"shop_{uuid.uuid4().hex[:12]}",
            "owner_id": "seed_owner_1",
            "name": "Himalayan Riders Leh",
            "description": "Premium bike rentals in the heart of Leh. 10+ years of serving adventurers on the world's highest motorable roads.",
            "address": "Main Bazaar Road, Leh, Ladakh 194101",
            "phone": "+91-9876543210",
            "rating": 4.5, "total_reviews": 0, "is_verified": True,
            "operating_hours": {"open": "07:00", "close": "21:00"},
            "created_at": now
        },
        {
            "shop_id": f"shop_{uuid.uuid4().hex[:12]}",
            "owner_id": "seed_owner_2",
            "name": "Nubra Valley Expeditions",
            "description": "Explore the hidden valleys of Ladakh. Bikes delivered to your hotel in Nubra, Pangong, or Turtuk.",
            "address": "Diskit, Nubra Valley, Ladakh 194401",
            "phone": "+91-9876543211",
            "rating": 4.3, "total_reviews": 0, "is_verified": True,
            "operating_hours": {"open": "08:00", "close": "20:00"},
            "created_at": now
        }
    ]

    for shop_doc in shops:
        await db.bike_shops.insert_one(shop_doc)

    for i, bike_data in enumerate(SEED_BIKES):
        shop = shops[0] if i < 5 else shops[1]
        bike_doc = {
            "bike_id": f"bike_{uuid.uuid4().hex[:12]}",
            "shop_id": shop["shop_id"],
            **bike_data,
            "is_available": True,
            "booking_slots": [],
            "cached_rating": 0,
            "cached_review_count": 0,
            "created_at": now,
            "updated_at": now
        }
        await db.bikes.insert_one(bike_doc)

    logger.info(f"Seeded {len(shops)} shops and {len(SEED_BIKES)} bikes")


@app.on_event("startup")
async def startup():
    global _background_task

    # ─── Database Indexes (designed for 50K+ users) ─────────
    # User indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("role")

    # Session indexes with TTL (auto-cleanup after 7 days)
    await db.user_sessions.create_index("session_token")
    await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)

    # Bike indexes for marketplace queries
    await db.bikes.create_index([("type", 1), ("location", 1), ("is_available", 1)])
    await db.bikes.create_index("bike_id", unique=True)
    await db.bikes.create_index("shop_id")
    await db.bikes.create_index([("daily_rate", 1)])
    await db.bikes.create_index([("brand", 1)])

    # Booking indexes for conflict detection and dashboard queries
    await db.bookings.create_index([("bike_id", 1), ("status", 1)])
    await db.bookings.create_index("customer_id")
    await db.bookings.create_index("booking_id", unique=True)
    await db.bookings.create_index([("shop_id", 1), ("status", 1)])
    await db.bookings.create_index([("status", 1), ("end_date", 1)])  # For overdue scan
    await db.bookings.create_index("referred_by")  # For travel agent queries

    # Shop indexes
    await db.bike_shops.create_index("owner_id")
    await db.bike_shops.create_index("shop_id", unique=True)

    # Review indexes
    await db.reviews.create_index("bike_id")
    await db.reviews.create_index("shop_id")
    await db.reviews.create_index([("booking_id", 1), ("reviewer_id", 1)])

    # Customer rating indexes (bidirectional)
    await db.customer_ratings.create_index("customer_id")
    await db.customer_ratings.create_index([("booking_id", 1), ("rated_by", 1)])

    # Notification indexes
    await db.notifications.create_index([("user_id", 1), ("is_read", 1)])
    await db.notifications.create_index([("user_id", 1), ("created_at", -1)])

    # Notification log (dedup for reminders)
    await db.notification_log.create_index([("booking_id", 1), ("type", 1)])

    # Payout and settlement indexes
    await db.payout_ledger.create_index([("shop_id", 1), ("status", 1)])
    await db.payout_ledger.create_index("booking_id")
    await db.settlements.create_index("shop_id")

    # Payment indexes
    await db.payments.create_index("booking_id")
    await db.payments.create_index("user_id")

    # Rating flags
    await db.rating_flags.create_index([("shop_id", 1), ("resolved", 1)])

    logger.info("Database indexes created (50K+ user scale)")
    await seed_database()

    # Start background scheduler
    _background_task = asyncio.create_task(background_scheduler())
    logger.info("Background scheduler started")


@app.on_event("shutdown")
async def shutdown():
    global _background_task
    if _background_task:
        _background_task.cancel()
        try:
            await _background_task
        except asyncio.CancelledError:
            pass
    client.close()
    logger.info("Shutdown complete")


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": "Ladakh Moto Market API", "version": "2.0.0"}
