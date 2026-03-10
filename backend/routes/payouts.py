"""
Payout & Settlement Routes — shop owner payout management.
"""
from fastapi import APIRouter, HTTPException, Request
from database import db
from routes.auth import get_current_user
from services.payout_engine import get_shop_payout_summary, get_shop_payout_ledger, process_settlement
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payouts", tags=["payouts"])


@router.get("/summary")
async def payout_summary(request: Request):
    """Get payout summary for the current shop owner."""
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="No shop found")
    return await get_shop_payout_summary(shop["shop_id"])


@router.get("/ledger")
async def payout_ledger(request: Request, status: str = None, page: int = 1, limit: int = 50):
    """Get paginated payout ledger for the current shop owner."""
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="No shop found")
    return await get_shop_payout_ledger(shop["shop_id"], status, page, limit)


@router.post("/settle")
async def settle_payouts(request: Request):
    """Process settlement for all pending payouts. Shop owner triggered."""
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="No shop found")
    result = await process_settlement(shop["shop_id"])
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/settlements")
async def list_settlements(request: Request):
    """List past settlements for the current shop."""
    user = await get_current_user(request)
    shop = await db.bike_shops.find_one({"owner_id": user["user_id"]}, {"_id": 0})
    if not shop:
        raise HTTPException(status_code=404, detail="No shop found")
    settlements = await db.settlements.find(
        {"shop_id": shop["shop_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"settlements": settlements}
