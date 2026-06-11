import logging
import os
import re
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError, jwt

from db.mongodb import get_db, _hash_password, _verify_password
from models.schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
    BudgetSetup,
    BudgetUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


def _create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse)
async def register(payload: UserCreate):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    username = payload.username.strip()
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise HTTPException(status_code=422, detail="Username must be alphanumeric")

    if db.users.find_one({"username": username}):
        raise HTTPException(status_code=409, detail="Username already taken")

    now = datetime.now(timezone.utc)
    try:
        result = db.users.insert_one(
            {
                "username": username,
                "password_hash": _hash_password(payload.password),
                "created_at": now,
                "onboarding_complete": False,
                "budget": {
                    "master_monthly": 0,
                    "categories": {
                        "food_dining_delivery": None,
                        "shopping_fashion": None,
                        "electronics_tech": None,
                        "entertainment_subs": None,
                        "health_lifestyle": None,
                        "others": None,
                    },
                    "month_set": now.strftime("%Y-%m"),
                },
                "wallet_state": {
                    "current": "calm",
                    "spend_pct": 0,
                    "last_calculated": None,
                    "state_since": now,
                },
                "streak": {"current_days": 0, "best_days": 0, "last_updated": now},
                "data_connections": {
                    "fivetran_connector_id": None,
                    "last_sync": None,
                    "sync_method": "manual",
                },
                "preferences": {
                    "notification_time": "09:00",
                    "timezone": "Asia/Kolkata",
                },
            }
        )
    except Exception as exc:
        logger.error("register: DB write failed: %s", exc)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    token = _create_token(str(result.inserted_id))
    return TokenResponse(access_token=token)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user = db.users.find_one({"username": payload.username})
    # Constant-time compare: always run verify even on missing user
    dummy_hash = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    stored_hash = user["password_hash"] if user else dummy_hash

    if not _verify_password(payload.password, stored_hash) or user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _create_token(str(user["_id"]))
    return TokenResponse(access_token=token)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/auth/logout")
async def logout(user_id: str = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


# ── Budget ────────────────────────────────────────────────────────────────────

@router.post("/budget/setup")
async def budget_setup(payload: BudgetSetup, user_id: str = Depends(get_current_user)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    now = datetime.now(timezone.utc)
    update: dict = {
        "budget.master_monthly": payload.master_monthly,
        "budget.month_set": now.strftime("%Y-%m"),
        "onboarding_complete": True,
    }
    if payload.categories:
        for field, val in payload.categories.model_dump().items():
            update[f"budget.categories.{field}"] = val

    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update})
    return {"message": "Budget set successfully"}


@router.put("/budget/update")
async def budget_update(payload: BudgetUpdate, user_id: str = Depends(get_current_user)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    update: dict = {}
    if payload.master_monthly is not None:
        update["budget.master_monthly"] = payload.master_monthly
    if payload.categories:
        for field, val in payload.categories.model_dump().items():
            if val is not None:
                update[f"budget.categories.{field}"] = val

    if update:
        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update})
    return {"message": "Budget updated"}


@router.delete("/auth/account")
async def delete_account(user_id: str = Depends(get_current_user)):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        oid = ObjectId(user_id)
        db.purchases.delete_many({"user_id": oid})
        db.nudges.delete_many({"user_id": oid})
        db.monthly_reports.delete_many({"user_id": oid})
        db.users.delete_one({"_id": oid})
    except Exception as exc:
        logger.error("delete_account failed for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Account deletion failed. Please try again.")

    return {"message": "Account deleted successfully"}


@router.get("/budget/current")
async def budget_current(user_id: str = Depends(get_current_user)):
    from datetime import date  # noqa: PLC0415
    from services.bigquery_service import get_monthly_total, get_category_breakdown  # noqa: PLC0415

    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).date()
    project_id = os.getenv("GCP_PROJECT_ID", "")

    master_monthly = float(user.get("budget", {}).get("master_monthly", 0) or 0)
    categories = user.get("budget", {}).get("categories", {})

    current_spend = await get_monthly_total(project_id, month_start)
    category_totals = await get_category_breakdown(project_id, month_start)

    spend_pct = (current_spend / master_monthly * 100) if master_monthly > 0 else 0.0
    default_cat = master_monthly / 6 if master_monthly > 0 else 1
    category_pcts = {
        cat: round((category_totals.get(cat, 0) / (categories.get(cat) or default_cat) * 100), 2)
        for cat in category_totals
    }

    streak = user.get("streak", {})
    return {
        "master_monthly": master_monthly,
        "categories": categories,
        "current_spend": current_spend,
        "spend_pct": round(spend_pct, 2),
        "category_pcts": category_pcts,
        "current_streak": int(streak.get("current_days", 0)),
        "best_streak": int(streak.get("best_days", 0)),
    }
