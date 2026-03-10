from fastapi import APIRouter, HTTPException, Response, Request
from database import db
from models import UserRegister, UserLogin
import bcrypt
import jwt
import uuid
import httpx
from datetime import datetime, timezone, timedelta
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

JWT_SECRET = os.environ.get('JWT_SECRET', 'ladakh-moto-jwt-secret-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


def create_jwt_token(user_id: str, email: str, role: str):
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def sanitize_user(user):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user.get("role", "customer"),
        "phone": user.get("phone", ""),
        "profile_picture": user.get("profile_picture", ""),
        "kyc_status": user.get("kyc_status", "pending"),
        "must_change_password": user.get("must_change_password", False),
        "created_at": user.get("created_at", "")
    }


async def get_current_user(request: Request):
    # Check cookie first
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one(
            {"session_token": session_token}, {"_id": 0}
        )
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one(
                    {"user_id": session["user_id"]}, {"_id": 0}
                )
                if user:
                    return user

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one(
                {"user_id": payload["user_id"]}, {"_id": 0}
            )
            if user:
                return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            # Try as session token
            session = await db.user_sessions.find_one(
                {"session_token": token}, {"_id": 0}
            )
            if session:
                expires_at = session.get("expires_at")
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at > datetime.now(timezone.utc):
                    user = await db.users.find_one(
                        {"user_id": session["user_id"]}, {"_id": 0}
                    )
                    if user:
                        return user

    raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/register")
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    user_doc = {
        "user_id": user_id,
        "email": data.email,
        "name": data.name,
        "password_hash": hashed,
        "role": data.role,
        "phone": data.phone,
        "profile_picture": "",
        "kyc_status": "pending",
        "created_at": now,
        "updated_at": now
    }
    await db.users.insert_one(user_doc)

    token = create_jwt_token(user_id, data.email, data.role)
    return {
        "token": token,
        "user": sanitize_user(user_doc)
    }


@router.post("/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Please use Google login")

    if not bcrypt.checkpw(data.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(user["user_id"], user["email"], user["role"])
    return {"token": token, "user": sanitize_user(user)}


@router.post("/session")
async def exchange_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as http_client:
        resp = await http_client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")

    auth_data = resp.json()
    email = auth_data["email"]
    name = auth_data.get("name", "")
    picture = auth_data.get("picture", "")
    session_token = auth_data.get("session_token", "")

    existing = await db.users.find_one({"email": email}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()

    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "profile_picture": picture, "updated_at": now}}
        )
        role = existing.get("role", "customer")
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        role = "customer"
        await db.users.insert_one({
            "user_id": user_id, "email": email, "name": name,
            "role": role, "phone": "", "profile_picture": picture,
            "kyc_status": "pending", "password_hash": "",
            "created_at": now, "updated_at": now
        })

    expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": expires_at, "created_at": now
    })

    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=7 * 24 * 60 * 60
    )

    user_data = {
        "user_id": user_id, "email": email, "name": name,
        "role": role, "phone": "", "profile_picture": picture,
        "kyc_status": "pending", "created_at": now
    }
    return {"user": user_data}


@router.get("/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return sanitize_user(user)


@router.put("/role")
async def update_role(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    new_role = body.get("role")
    if new_role not in ["customer", "shop_owner", "travel_agent"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"role": new_role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Role updated", "role": new_role}


@router.post("/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
        response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out"}


@router.post("/change-password")
async def change_password(request: Request):
    """Change password (used for first-login forced password change)."""
    user = await get_current_user(request)
    body = await request.json()
    new_password = body.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "password_hash": hashed,
            "must_change_password": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Password changed successfully"}
