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

    # Check for similar item in purchase history (stub: False for now)
    has_similar = False
    similar_item = payload.context.get("similar_item") if payload.context else None
    if similar_item:
        has_similar = True

    tier = calculate_nudge_tier(spend_pct, has_similar)
    copy = await generate_nudge_copy(
        state=state,
        spend_pct=spend_pct,
        platform=payload.platform,
        similar_item=similar_item,
        days_since=payload.context.get("days_since") if payload.context else None,
        category_pct=max(wallet["category_pcts"].values()) if wallet["category_pcts"] else 0.0,
    )

    now = datetime.now(timezone.utc)
    nudge_doc = {
        "user_id": ObjectId(user_id),
        "fired_at": now,
        "tier": tier,
        "trigger_type": payload.trigger_type,
        "wallet_state_at_fire": state,
        "spend_pct_at_fire": spend_pct,
        "context": {
            "platform": payload.platform,
            "similar_item": similar_item,
            "similar_item_order_date": None,
            "days_since_similar": payload.context.get("days_since") if payload.context else None,
            "category_pct": max(wallet["category_pcts"].values()) if wallet["category_pcts"] else 0.0,
            "master_pct": spend_pct,
        },
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
        context=nudge_doc["context"],
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
        nudge = db.nudges.find_one({"_id": ObjectId(payload.nudge_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Nudge not found")

    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found")

    if str(nudge["user_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.now(timezone.utc)
    db.nudges.update_one(
        {"_id": ObjectId(payload.nudge_id)},
        {"$set": {"user_response": payload.response, "responded_at": now}},
    )

    # Update streak
    user = db.users.find_one({"_id": ObjectId(user_id)})
    streak = user.get("streak", {}) if user else {}
    current_days = int(streak.get("current_days", 0))
    best_days = int(streak.get("best_days", 0))

    if payload.response == "paused":
        current_days += 1
        best_days = max(best_days, current_days)
        message = f"Nice one! Streak: {current_days} days 🔥"
    elif payload.response == "overridden" and nudge.get("tier") == "hard":
        current_days = 0
        message = "Streak reset. Start fresh tomorrow 💪"
    else:
        message = "Response logged"

    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "streak.current_days": current_days,
                "streak.best_days": best_days,
                "streak.last_updated": now,
            }
        },
    )

    return {"streak_days": current_days, "message": message}


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
