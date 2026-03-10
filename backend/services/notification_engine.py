"""
Notification Engine — smart notification orchestration.

Triggers notifications across channels: in_app, sms, email, push.
Handles booking lifecycle events, reminders, and preferences.
"""
from database import db
from adapters import sms_provider, email_provider, push_provider
import uuid
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# ─── Notification Types & Templates ────────────────────────

TEMPLATES = {
    "booking_confirmed": {
        "title": "Booking Confirmed!",
        "sms": "Your {bike_name} booking is confirmed for {start_date} to {end_date}. Shop: {shop_name}.",
        "email_subject": "Booking Confirmed - {bike_name}",
        "email_body": "Hi {customer_name},\n\nYour booking for {bike_name} is confirmed.\nDates: {start_date} to {end_date}\nShop: {shop_name}\nTotal: {total_amount} INR\n\nSafe riding!",
        "channels": ["in_app", "sms", "email"]
    },
    "new_booking": {
        "title": "New Booking Received!",
        "sms": "New booking: {customer_name} booked {bike_name} for {start_date} to {end_date}.",
        "email_subject": "New Booking - {bike_name}",
        "email_body": "New booking received:\nCustomer: {customer_name}\nBike: {bike_name}\nDates: {start_date} to {end_date}\nAmount: {total_amount} INR",
        "channels": ["in_app", "sms", "email"]
    },
    "booking_reminder_24h": {
        "title": "Pickup Tomorrow!",
        "sms": "Reminder: Your {bike_name} pickup is tomorrow at {shop_name}. Address: {shop_address}.",
        "email_subject": "Pickup Reminder - {bike_name} Tomorrow",
        "email_body": "Hi {customer_name},\n\nReminder: Your {bike_name} is ready for pickup tomorrow.\nShop: {shop_name}\nAddress: {shop_address}",
        "channels": ["in_app", "sms", "email", "push"]
    },
    "return_reminder_4h": {
        "title": "Return Due in 4 Hours",
        "sms": "Your {bike_name} is due for return in 4 hours. Late return penalty: 1.5x daily rate.",
        "email_subject": "Return Reminder - {bike_name}",
        "email_body": "Hi {customer_name},\n\nYour {bike_name} rental ends in 4 hours.\nPlease return to {shop_name} to avoid late penalties.\n\nPenalty rate: 1.5x daily rate per extra day.",
        "channels": ["in_app", "sms", "push"]
    },
    "booking_overdue": {
        "title": "Booking Overdue!",
        "sms": "OVERDUE: Your {bike_name} was due for return. Late penalty is accruing at {daily_rate} * 1.5x/day.",
        "email_subject": "OVERDUE - Return {bike_name} Immediately",
        "email_body": "Hi {customer_name},\n\nYour {bike_name} rental is OVERDUE.\nPenalty rate: {daily_rate} * 1.5x per extra day.\nPlease return immediately to {shop_name}.",
        "channels": ["in_app", "sms", "email", "push"]
    },
    "booking_completed": {
        "title": "Ride Complete!",
        "sms": "Thanks for riding! Your {bike_name} rental is complete. Leave a review!",
        "email_subject": "Ride Complete - Rate Your Experience",
        "email_body": "Hi {customer_name},\n\nYour {bike_name} ride is complete!\nTotal: {total_amount} INR\n\nWe'd love your review. Rate your experience on the platform.",
        "channels": ["in_app", "email"]
    },
    "penalty_applied": {
        "title": "Late Return Penalty Applied",
        "sms": "Late return penalty of {penalty_amount} INR applied to your {bike_name} booking.",
        "email_subject": "Late Return Penalty - {penalty_amount} INR",
        "email_body": "Hi {customer_name},\n\nA late return penalty of {penalty_amount} INR has been applied.\nExtra days: {extra_days}\nRate: 1.5x daily rate",
        "channels": ["in_app", "sms", "email"]
    },
    "payout_processed": {
        "title": "Payout Processed!",
        "sms": "Payout of {payout_amount} INR has been processed for your shop {shop_name}.",
        "email_subject": "Payout Processed - {payout_amount} INR",
        "email_body": "Hi {owner_name},\n\nYour payout of {payout_amount} INR has been processed.\nCommission: {commission_amount} INR\nNet amount: {net_amount} INR",
        "channels": ["in_app", "email"]
    },
    "review_received": {
        "title": "New Review Received",
        "sms": "",
        "email_subject": "New Review for {bike_name}",
        "email_body": "New {rating}-star review for {bike_name}: {comment}",
        "channels": ["in_app"]
    },
    "booking_cancelled": {
        "title": "Booking Cancelled",
        "sms": "Your {bike_name} booking has been cancelled. Refund: {refund_amount} INR.",
        "email_subject": "Booking Cancelled - {bike_name}",
        "email_body": "Hi {customer_name},\n\nYour booking for {bike_name} has been cancelled.\nRefund amount: {refund_amount} INR",
        "channels": ["in_app", "email"]
    },
    "customer_rating": {
        "title": "You've Been Rated!",
        "sms": "",
        "email_subject": "",
        "email_body": "",
        "channels": ["in_app"]
    }
}


async def create_in_app_notification(user_id: str, notif_type: str, title: str, message: str, data: dict = None) -> str:
    """Create an in-app notification. Returns notification_id."""
    notif_id = f"notif_{uuid.uuid4().hex[:12]}"
    await db.notifications.insert_one({
        "notification_id": notif_id,
        "user_id": user_id, "type": notif_type,
        "title": title, "message": message,
        "data": data or {}, "is_read": False,
        "channel": "in_app",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return notif_id


async def get_user_notification_prefs(user_id: str) -> dict:
    """Get user's notification channel preferences."""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "notification_prefs": 1, "phone": 1, "email": 1})
    prefs = (user or {}).get("notification_prefs", {})
    return {
        "in_app": prefs.get("in_app", True),
        "sms": prefs.get("sms", True) and bool((user or {}).get("phone")),
        "email": prefs.get("email", True) and bool((user or {}).get("email")),
        "push": prefs.get("push", False),  # Requires device token
        "phone": (user or {}).get("phone", ""),
        "email_address": (user or {}).get("email", ""),
    }


def render_template(template_str: str, variables: dict) -> str:
    """Simple {variable} template rendering."""
    result = template_str
    for key, val in variables.items():
        result = result.replace(f"{{{key}}}", str(val))
    return result


async def dispatch_notification(user_id: str, notif_type: str, variables: dict, extra_data: dict = None):
    """
    Smart notification dispatcher.
    1. Looks up template
    2. Checks user preferences per channel
    3. Dispatches to all enabled channels
    """
    template = TEMPLATES.get(notif_type)
    if not template:
        logger.warning(f"Unknown notification type: {notif_type}")
        return

    prefs = await get_user_notification_prefs(user_id)
    channels = template["channels"]
    dispatched = []

    for channel in channels:
        if not prefs.get(channel, False):
            continue

        if channel == "in_app":
            title = template["title"]
            message_body = render_template(template.get("sms", template["title"]), variables)
            await create_in_app_notification(user_id, notif_type, title, message_body, extra_data)
            dispatched.append("in_app")

        elif channel == "sms" and template.get("sms"):
            sms_text = render_template(template["sms"], variables)
            await sms_provider.send_sms(prefs["phone"], sms_text)
            dispatched.append("sms")

        elif channel == "email" and template.get("email_subject"):
            subject = render_template(template["email_subject"], variables)
            body = render_template(template["email_body"], variables)
            await email_provider.send_email(prefs["email_address"], subject, body)
            dispatched.append("email")

        elif channel == "push":
            device_token = await _get_device_token(user_id)
            if device_token:
                await push_provider.send_push(device_token, template["title"], render_template(template.get("sms", ""), variables), extra_data)
                dispatched.append("push")

    logger.info(f"[NOTIF] {notif_type} → user {user_id} via [{', '.join(dispatched)}]")
    return dispatched


async def _get_device_token(user_id: str) -> str:
    """Get push notification device token for user."""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "device_token": 1})
    return (user or {}).get("device_token", "")


async def scan_and_send_reminders() -> dict:
    """
    Background task: scan for bookings needing reminders.
    - 24h before pickup: send reminder
    - 4h before return: send reminder
    Returns counts of reminders sent.
    """
    now = datetime.now(timezone.utc)
    sent = {"pickup_24h": 0, "return_4h": 0}

    # Pickup reminders (24h before start)
    tomorrow_start = (now + timedelta(hours=23)).isoformat()
    tomorrow_end = (now + timedelta(hours=25)).isoformat()
    upcoming = await db.bookings.find({
        "status": "confirmed",
        "start_date": {"$gte": tomorrow_start, "$lte": tomorrow_end}
    }, {"_id": 0}).to_list(100)

    for booking in upcoming:
        already_sent = await db.notification_log.find_one({
            "booking_id": booking["booking_id"], "type": "booking_reminder_24h"
        })
        if already_sent:
            continue
        await dispatch_notification(booking["customer_id"], "booking_reminder_24h", {
            "bike_name": booking.get("bike_name", ""),
            "shop_name": booking.get("shop_name", ""),
            "shop_address": "",
            "customer_name": ""
        }, {"booking_id": booking["booking_id"]})
        await db.notification_log.insert_one({
            "booking_id": booking["booking_id"], "type": "booking_reminder_24h",
            "sent_at": now.isoformat()
        })
        sent["pickup_24h"] += 1

    # Return reminders (4h before end)
    four_h_start = (now + timedelta(hours=3)).isoformat()
    four_h_end = (now + timedelta(hours=5)).isoformat()
    ending_soon = await db.bookings.find({
        "status": "active",
        "end_date": {"$gte": four_h_start, "$lte": four_h_end}
    }, {"_id": 0}).to_list(100)

    for booking in ending_soon:
        already_sent = await db.notification_log.find_one({
            "booking_id": booking["booking_id"], "type": "return_reminder_4h"
        })
        if already_sent:
            continue
        await dispatch_notification(booking["customer_id"], "return_reminder_4h", {
            "bike_name": booking.get("bike_name", ""),
            "shop_name": booking.get("shop_name", ""),
            "customer_name": "",
            "daily_rate": str(booking.get("daily_rate", 0))
        }, {"booking_id": booking["booking_id"]})
        await db.notification_log.insert_one({
            "booking_id": booking["booking_id"], "type": "return_reminder_4h",
            "sent_at": now.isoformat()
        })
        sent["return_4h"] += 1

    if sent["pickup_24h"] or sent["return_4h"]:
        logger.info(f"[REMINDERS] Sent {sent['pickup_24h']} pickup + {sent['return_4h']} return reminders")
    return sent
