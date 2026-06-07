from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from db.mongodb import get_db
from models.schemas import PurchaseManual
from routers.auth import get_current_user

router = APIRouter(prefix="/purchases", tags=["purchases"])

CONSUMABLE_CATEGORIES = {"food_dining_delivery", "health_lifestyle"}


@router.post("/screenshot")
async def upload_screenshot(user_id: str = Depends(get_current_user)):
    return {"status": "stub", "message": "Gemini Vision — implemented in Session 2"}


@router.post("/manual")
async def add_manual_purchase(
    payload: PurchaseManual,
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    now = datetime.now(timezone.utc)
    order_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    is_consumable = payload.category in CONSUMABLE_CATEGORIES

    # Deduplication check
    existing = db.purchases.find_one(
        {
            "user_id": ObjectId(user_id),
            "item_name": payload.item_name,
            "platform": payload.platform,
            "amount": payload.amount,
            "order_date": order_date,
        }
    )
    if existing:
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    try:
        result = db.purchases.insert_one(
            {
                "user_id": ObjectId(user_id),
                "item_name": payload.item_name,
                "item_description": payload.item_name,
                "platform": payload.platform,
                "amount": payload.amount,
                "category": payload.category,
                "subcategory": None,
                "order_date": order_date,
                "capture_date": now,
                "capture_method": "manual",
                "raw_extracted_text": None,
                "gemini_tags": [],
                "embedding_summary": None,
                "is_consumable": is_consumable,
                "order_date_confidence": "estimated",
            }
        )
    except Exception:
        # Unique index violation = duplicate
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    return {"status": "saved", "purchase_id": str(result.inserted_id)}


@router.post("/check")
async def pre_purchase_check(user_id: str = Depends(get_current_user)):
    return {"is_clear": True, "message": "Full check — implemented in Session 2"}


@router.get("/history")
async def purchase_history(user_id: str = Depends(get_current_user)):
    db = get_db()
    if db is None:
        return {"purchases": []}

    from datetime import timedelta  # noqa: PLC0415

    sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
    cursor = db.purchases.find(
        {"user_id": ObjectId(user_id), "order_date": {"$gte": sixty_days_ago}},
        sort=[("order_date", -1)],
    )
    purchases = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        if doc.get("order_date"):
            doc["order_date"] = doc["order_date"].isoformat()
        if doc.get("capture_date"):
            doc["capture_date"] = doc["capture_date"].isoformat()
        purchases.append(doc)

    return {"purchases": purchases}
