"""
Payout Engine — commission calculation, settlement processing, ledger management.

Commission structure:
  Platform takes 10% on each booking.
  Remaining 90% goes to shop owner.
  Payouts are batched and processed periodically.
"""
from database import db
from adapters import payment_gateway
from services.notification_engine import dispatch_notification
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

COMMISSION_RATE = 0.10  # 10% platform commission


async def create_payout_entry(shop_id: str, booking_id: str, gross_amount: float) -> dict:
    """Create a payout ledger entry when a booking is paid."""
    commission = gross_amount * COMMISSION_RATE
    net_amount = gross_amount - commission
    now = datetime.now(timezone.utc).isoformat()

    payout_doc = {
        "payout_id": f"payout_{uuid.uuid4().hex[:12]}",
        "shop_id": shop_id,
        "booking_id": booking_id,
        "gross_amount": gross_amount,
        "amount": net_amount,
        "commission_rate": COMMISSION_RATE,
        "commission_amount": commission,
        "status": "pending",
        "payout_date": None,
        "gateway_reference": None,
        "created_at": now,
        "updated_at": now
    }
    await db.payout_ledger.insert_one(payout_doc)
    result = {k: v for k, v in payout_doc.items() if k != "_id"}
    logger.info(f"[PAYOUT] Created: {result['payout_id']} shop={shop_id} net={net_amount}")
    return result


async def get_shop_payout_summary(shop_id: str) -> dict:
    """Get payout summary for a shop."""
    pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {
            "_id": "$status",
            "total_amount": {"$sum": "$amount"},
            "total_commission": {"$sum": "$commission_amount"},
            "total_gross": {"$sum": "$gross_amount"},
            "count": {"$sum": 1}
        }}
    ]
    result = await db.payout_ledger.aggregate(pipeline).to_list(10)
    summary = {}
    for r in result:
        summary[r["_id"]] = {
            "count": r["count"],
            "net_amount": r["total_amount"],
            "commission": r["total_commission"],
            "gross_amount": r["total_gross"]
        }

    # Grand totals
    total_pipeline = [
        {"$match": {"shop_id": shop_id}},
        {"$group": {
            "_id": None,
            "total_gross": {"$sum": "$gross_amount"},
            "total_net": {"$sum": "$amount"},
            "total_commission": {"$sum": "$commission_amount"},
            "count": {"$sum": 1}
        }}
    ]
    totals = await db.payout_ledger.aggregate(total_pipeline).to_list(1)

    return {
        "shop_id": shop_id,
        "by_status": summary,
        "totals": {
            "gross_revenue": totals[0]["total_gross"] if totals else 0,
            "net_payable": totals[0]["total_net"] if totals else 0,
            "commission_paid": totals[0]["total_commission"] if totals else 0,
            "total_entries": totals[0]["count"] if totals else 0
        }
    }


async def get_shop_payout_ledger(shop_id: str, status: str = None, page: int = 1, limit: int = 50) -> dict:
    """Get paginated payout ledger for a shop."""
    query = {"shop_id": shop_id}
    if status:
        query["status"] = status

    skip = (page - 1) * limit
    entries = await db.payout_ledger.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.payout_ledger.count_documents(query)

    # Enrich with booking info
    for entry in entries:
        booking = await db.bookings.find_one(
            {"booking_id": entry["booking_id"]},
            {"_id": 0, "bike_name": 1, "customer_id": 1, "start_date": 1, "end_date": 1}
        )
        if booking:
            entry["bike_name"] = booking.get("bike_name", "")
            entry["booking_dates"] = f"{booking.get('start_date', '')[:10]} to {booking.get('end_date', '')[:10]}"
            customer = await db.users.find_one({"user_id": booking["customer_id"]}, {"_id": 0, "name": 1})
            entry["customer_name"] = customer["name"] if customer else ""

    return {"entries": entries, "total": total, "page": page, "limit": limit}


async def process_settlement(shop_id: str) -> dict:
    """Process all pending payouts for a shop into a single settlement."""
    pending = await db.payout_ledger.find(
        {"shop_id": shop_id, "status": "pending"}, {"_id": 0}
    ).to_list(500)

    if not pending:
        return {"message": "No pending payouts", "amount": 0}

    total_amount = sum(p["amount"] for p in pending)
    total_commission = sum(p["commission_amount"] for p in pending)
    now = datetime.now(timezone.utc).isoformat()

    # Process payout via adapter
    result = await payment_gateway.create_payout(shop_id, total_amount, "INR")

    if result.success:
        payout_ids = [p["payout_id"] for p in pending]
        await db.payout_ledger.update_many(
            {"payout_id": {"$in": payout_ids}},
            {"$set": {
                "status": "processed",
                "payout_date": now,
                "gateway_reference": result.reference,
                "updated_at": now
            }}
        )

        # Record settlement
        settlement_id = f"settle_{uuid.uuid4().hex[:12]}"
        await db.settlements.insert_one({
            "settlement_id": settlement_id,
            "shop_id": shop_id,
            "payout_ids": payout_ids,
            "total_amount": total_amount,
            "total_commission": total_commission,
            "gateway_reference": result.reference,
            "status": "completed",
            "created_at": now
        })

        # Notify shop owner
        shop = await db.bike_shops.find_one({"shop_id": shop_id}, {"_id": 0, "owner_id": 1, "name": 1})
        if shop:
            await dispatch_notification(shop["owner_id"], "payout_processed", {
                "payout_amount": str(total_amount),
                "shop_name": shop["name"],
                "commission_amount": str(total_commission),
                "net_amount": str(total_amount),
                "owner_name": ""
            }, {"settlement_id": settlement_id})

        logger.info(f"[SETTLEMENT] {shop_id}: {len(payout_ids)} payouts, {total_amount} INR")
        return {
            "settlement_id": settlement_id,
            "payouts_processed": len(payout_ids),
            "total_amount": total_amount,
            "total_commission": total_commission,
            "gateway_reference": result.reference
        }

    logger.error(f"[SETTLEMENT] Failed for {shop_id}: {result.message}")
    return {"error": "Settlement processing failed", "message": result.message}
