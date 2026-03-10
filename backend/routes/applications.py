"""
Application Routes — Shop owner and Travel agent onboarding applications.
Public form submission + admin review with email credential delivery.
"""
from fastapi import APIRouter, HTTPException, Request
from database import db
from routes.auth import get_current_user, create_jwt_token
import resend
import asyncio
import bcrypt
import uuid
import string
import random
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/applications", tags=["applications"])

resend.api_key = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")


def generate_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


async def send_credentials_email(to_email: str, name: str, password: str, role: str):
    """Send login credentials to approved user via Resend."""
    role_label = "Shop Owner" if role == "shop_owner" else "Travel Agent"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#09090b;color:#fafafa;padding:32px;border:1px solid #27272a;">
        <h1 style="color:#eab308;font-size:24px;margin-bottom:8px;">Welcome to Ladakh Moto Market</h1>
        <p style="color:#a1a1aa;font-size:14px;margin-bottom:24px;">Your {role_label} application has been approved!</p>
        <div style="background:#18181b;padding:20px;border:1px solid #27272a;margin-bottom:24px;">
            <p style="margin:0 0 8px;font-size:14px;">Hi <strong>{name}</strong>,</p>
            <p style="margin:0 0 16px;font-size:14px;color:#a1a1aa;">Here are your login credentials:</p>
            <p style="margin:0 0 4px;font-size:14px;"><strong>Email:</strong> {to_email}</p>
            <p style="margin:0 0 4px;font-size:14px;"><strong>Password:</strong> <code style="background:#27272a;padding:2px 8px;border-radius:2px;color:#eab308;">{password}</code></p>
            <p style="margin:16px 0 0;font-size:12px;color:#a1a1aa;">You will be asked to change your password on first login.</p>
        </div>
        <p style="font-size:12px;color:#a1a1aa;">— Ladakh Moto Market Team</p>
    </div>
    """
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": f"Ladakh Moto Market — Your {role_label} Account is Ready",
            "html": html
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"[EMAIL] Credentials sent to {to_email}, id={result.get('id', 'N/A')}")
        return True
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send to {to_email}: {e}")
        return False


@router.post("/submit")
async def submit_application(request: Request):
    """Public endpoint: submit a shop owner or travel agent application."""
    body = await request.json()

    required = ["name", "email", "phone", "application_type"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"{field} is required")

    app_type = body["application_type"]
    if app_type not in ["shop_owner", "travel_agent"]:
        raise HTTPException(status_code=400, detail="Invalid application type")

    existing = await db.users.find_one({"email": body["email"]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="This email is already registered")

    existing_app = await db.applications.find_one(
        {"email": body["email"], "status": "pending"}, {"_id": 0}
    )
    if existing_app:
        raise HTTPException(status_code=400, detail="An application with this email is already pending")

    now = datetime.now(timezone.utc).isoformat()
    app_doc = {
        "application_id": f"app_{uuid.uuid4().hex[:12]}",
        "application_type": app_type,
        "name": body["name"],
        "email": body["email"],
        "phone": body["phone"],
        "status": "pending",
        "created_at": now,
        "updated_at": now,
    }

    if app_type == "shop_owner":
        app_doc["shop_name"] = body.get("shop_name", "")
        app_doc["shop_address"] = body.get("shop_address", "")
        app_doc["total_bikes"] = body.get("total_bikes", 0)
        app_doc["bike_types"] = body.get("bike_types", "")
        app_doc["experience_years"] = body.get("experience_years", 0)
        app_doc["description"] = body.get("description", "")
    else:
        app_doc["agency_name"] = body.get("agency_name", "")
        app_doc["agency_address"] = body.get("agency_address", "")
        app_doc["agency_type"] = body.get("agency_type", "travel_agency")
        app_doc["description"] = body.get("description", "")

    await db.applications.insert_one(app_doc)
    result = {k: v for k, v in app_doc.items() if k != "_id"}
    return {"message": "Application submitted successfully", "application": result}


@router.get("")
async def list_applications(request: Request, status: str = None,
                            application_type: str = None, page: int = 1, limit: int = 20):
    """Admin: list all applications."""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {}
    if status:
        query["status"] = status
    if application_type:
        query["application_type"] = application_type

    skip = (page - 1) * limit
    total = await db.applications.count_documents(query)
    apps = await db.applications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    return {"applications": apps, "total": total, "page": page, "limit": limit}


@router.post("/{application_id}/approve")
async def approve_application(application_id: str, request: Request):
    """Admin: approve an application — creates user account and sends credentials."""
    admin = await get_current_user(request)
    if admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    app = await db.applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["status"] != "pending":
        raise HTTPException(status_code=400, detail="Application already processed")

    # Check if email already registered
    existing = await db.users.find_one({"email": app["email"]}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # Generate random password and create user
    password = generate_password()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    role = app["application_type"]

    user_doc = {
        "user_id": user_id,
        "email": app["email"],
        "name": app["name"],
        "password_hash": hashed,
        "role": role,
        "phone": app["phone"],
        "profile_picture": "",
        "kyc_status": "approved",
        "must_change_password": True,
        "created_at": now,
        "updated_at": now,
    }
    await db.users.insert_one(user_doc)

    # If shop owner, create the shop
    if role == "shop_owner" and app.get("shop_name"):
        shop_doc = {
            "shop_id": f"shop_{uuid.uuid4().hex[:12]}",
            "owner_id": user_id,
            "name": app["shop_name"],
            "description": app.get("description", ""),
            "address": app.get("shop_address", ""),
            "phone": app["phone"],
            "rating": 0,
            "total_reviews": 0,
            "is_verified": True,
            "operating_hours": {"open": "08:00", "close": "20:00"},
            "created_at": now,
        }
        await db.bike_shops.insert_one(shop_doc)

    # Update application status
    await db.applications.update_one(
        {"application_id": application_id},
        {"$set": {
            "status": "approved",
            "approved_by": admin["user_id"],
            "approved_at": now,
            "generated_user_id": user_id,
            "updated_at": now,
        }}
    )

    # Send email with credentials
    email_sent = await send_credentials_email(app["email"], app["name"], password, role)

    return {
        "message": "Application approved",
        "user_id": user_id,
        "email_sent": email_sent,
        "generated_password": password,
    }


@router.post("/{application_id}/reject")
async def reject_application(application_id: str, request: Request):
    """Admin: reject an application."""
    admin = await get_current_user(request)
    if admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    body = await request.json()
    app = await db.applications.find_one({"application_id": application_id}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app["status"] != "pending":
        raise HTTPException(status_code=400, detail="Application already processed")

    now = datetime.now(timezone.utc).isoformat()
    await db.applications.update_one(
        {"application_id": application_id},
        {"$set": {
            "status": "rejected",
            "rejected_by": admin["user_id"],
            "rejection_reason": body.get("reason", ""),
            "updated_at": now,
        }}
    )
    return {"message": "Application rejected"}
