from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from db.bigquery import get_bigquery_client
from db.mongodb import get_db
from middleware.security import limiter
from models.schemas import NudgeFireRequest, NudgeRespondRequest, NudgeResponse
from routers.auth import get_current_user
from services.analysis_service import get_full_wallet_state, calculate_nudge_tier
from services.gemini_service import generate_nudge_copy

router = APIRouter(prefix="/nudges", tags=["nudges"])

FASHION_PLATFORMS = {"myntra", "ajio", "meesho", "nykaa"}
QC_PLATFORMS      = {"zepto", "blinkit", "swiggy"}


@router.post("/fire", response_model=NudgeResponse)
@limiter.limit("10/minute")
async def fire_nudge(
    request: Request,
    payload: NudgeFireRequest,
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    bq_client = get_bigquery_client()

    wallet = await get_full_wallet_state(user_id, db, bq_client)
    state = wallet["state"]
    spend_pct = wallet["spend_pct"]
    category_pcts = wallet.get("category_pcts", {})

    ctx = payload.context or {}
    similar_item = ctx.get("similar_item")
    days_since = ctx.get("days_since")

    # Resolve category_pct: use explicit context value, then platform-based lookup,
    # then None for general apps — never fall back to max() across all categories.
    platform_lower = (payload.platform or "").lower()
    ctx_category_pct = ctx.get("category_pct")  # None when missing or explicitly null

    if ctx_category_pct is not None:
        category_pct: float | None = float(ctx_category_pct)
    elif payload.trigger_type == "pre_shop_check" and platform_lower in FASHION_PLATFORMS:
        category_pct = category_pcts.get("shopping_fashion")
    elif payload.trigger_type == "pre_shop_check" and platform_lower in QC_PLATFORMS:
        category_pct = category_pcts.get("food_dining_delivery")
    else:
        category_pct = None  # general apps (Amazon, Flipkart) — use master_pct only

    has_similar = similar_item is not None
    tier = calculate_nudge_tier(spend_pct, has_similar, float(category_pct or 0))

    copy = await generate_nudge_copy(
        state=state,
        spend_pct=spend_pct,
        platform=payload.platform,
        similar_item=similar_item,
        days_since=days_since,
        category_pct=category_pct,
    )

    now = datetime.now(timezone.utc)
    nudge_ctx = {
        "platform": payload.platform,
        "similar_item": similar_item,
        "similar_item_order_date": None,
        "days_since_similar": days_since,
        "category_pct": float(category_pct) if category_pct is not None else None,
        "master_pct": spend_pct,
    }

    nudge_doc = {
        "user_id": ObjectId(user_id),
        "fired_at": now,
        "tier": tier,
        "trigger_type": payload.trigger_type,
        "wallet_state_at_fire": state,
        "spend_pct_at_fire": spend_pct,
        "context": nudge_ctx,
        "gemini_copy": copy,
        "user_response": "pending",
        "responded_at": None,
        "transaction_followed": None,
        "amount_after_nudge": None,
    }

    nudge_id = "offline"
    if db is not None:
        result = db.nudges.insert_one(nudge_doc)
        nudge_id = str(result.inserted_id)

    return NudgeResponse(
        nudge_id=nudge_id,
        tier=tier,
        state=state,
        title=copy["title"],
        body=copy["body"],
        tag=copy["tag"],
        context=nudge_ctx,
    )


@router.post("/respond")
async def respond_to_nudge(
    payload: NudgeRespondRequest,
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        nudge = db.nudges.find_one({"_id": ObjectId(payload.nudge_id), "user_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Nudge not found")

    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")

    if nudge.get("user_response") not in (None, "pending"):
        raise HTTPException(status_code=400, detail="Already responded to this nudge")

    now = datetime.now(timezone.utc)
    db.nudges.update_one(
        {"_id": ObjectId(payload.nudge_id)},
        {"$set": {"user_response": payload.response, "responded_at": now}},
    )

    user = db.users.find_one({"_id": ObjectId(user_id)})
    streak = (user or {}).get("streak", {})
    current_days = int(streak.get("current_days", 0))
    best_days = int(streak.get("best_days", 0))

    if payload.response == "paused":
        current_days += 1
        best_days = max(best_days, current_days)
        day_label = "day" if current_days == 1 else "days"
        message = f"Nice one! Streak: {current_days} {day_label} 🔥"
    elif payload.response == "overridden":
        if nudge.get("tier") == "hard":
            current_days = 0
            message = "Streak reset. Start fresh tomorrow 💪"
        else:
            message = "Got it. No streak impact for this one."
    else:
        message = "Response logged"

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "streak.current_days": current_days,
            "streak.best_days": best_days,
            "streak.last_updated": now,
        }},
    )

    return {"streak_days": current_days, "message": message, "best_streak": best_days}


@router.get("/history")
async def nudge_history(user_id: str = Depends(get_current_user)):
    db = get_db()
    if db is None:
        return {"nudges": []}

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    cursor = db.nudges.find(
        {"user_id": ObjectId(user_id), "fired_at": {"$gte": month_start}},
        sort=[("fired_at", -1)],
    )
    nudges = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        if doc.get("fired_at"):
            doc["fired_at"] = doc["fired_at"].isoformat()
        nudges.append(doc)

    return {"nudges": nudges}
