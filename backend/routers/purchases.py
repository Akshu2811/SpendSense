from datetime import datetime, timezone, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from db.bigquery import get_bigquery_client
from db.mongodb import get_db
from models.schemas import PurchaseManual
from routers.auth import get_current_user
from services.analysis_service import get_full_wallet_state
from services.gemini_service import (
    check_duplicate_purchase,
    extract_from_multiple_screenshots,
    extract_product_for_check,
    extract_purchase_from_screenshot,
)

router = APIRouter(prefix="/purchases", tags=["purchases"])

CONSUMABLE_CATEGORIES = {"food_dining_delivery"}
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _serialize_purchase(doc: dict) -> dict:
    """Return a client-safe purchase document (no raw_extracted_text)."""
    out = {k: v for k, v in doc.items() if k != "raw_extracted_text"}
    out["_id"] = str(out["_id"])
    out["user_id"] = str(out["user_id"])
    if out.get("order_date"):
        out["order_date"] = out["order_date"].isoformat()
    if out.get("capture_date"):
        out["capture_date"] = out["capture_date"].isoformat()
    return out


def _build_purchase_doc(user_id: str, extracted: dict, capture_method: str) -> dict:
    now = datetime.now(timezone.utc)
    order_date_str = extracted.get("order_date")
    if order_date_str:
        try:
            from datetime import date  # noqa: PLC0415
            d = datetime.strptime(order_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            order_date = d
        except ValueError:
            order_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        order_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    is_consumable = bool(extracted.get("is_consumable", False)) or \
                    extracted.get("category", "") in CONSUMABLE_CATEGORIES

    return {
        "user_id": ObjectId(user_id),
        "item_name": extracted.get("item_name", "Unknown Item"),
        "item_description": extracted.get("item_description") or extracted.get("item_name", ""),
        "platform": extracted.get("platform", "Other"),
        "amount": float(extracted.get("amount", 0)),
        "category": extracted.get("category", "others"),
        "subcategory": extracted.get("subcategory"),
        "order_date": order_date,
        "capture_date": now,
        "capture_method": capture_method,
        "raw_extracted_text": extracted.get("raw_extracted_text"),
        "gemini_tags": [],
        "embedding_summary": None,
        "is_consumable": is_consumable,
        "order_date_confidence": extracted.get("order_date_confidence", "estimated"),
    }


def _check_dedup(db, user_id: str, doc: dict) -> bool:
    """Return True if this purchase already exists in MongoDB."""
    existing = db.purchases.find_one({
        "user_id": ObjectId(user_id),
        "item_name": doc["item_name"],
        "platform": doc["platform"],
        "amount": doc["amount"],
        "order_date": doc["order_date"],
    })
    return existing is not None


# ── Screenshot upload ─────────────────────────────────────────────────────────

@router.post("/screenshot")
async def upload_screenshot(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Validate file type
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images accepted")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5MB.")

    mime = file.content_type or "image/jpeg"
    extracted = await extract_purchase_from_screenshot(image_bytes, mime_type=mime)

    if extracted.get("error"):
        return {
            "status": "extraction_failed",
            "message": "Couldn't read this image. Try a clearer screenshot or add manually.",
        }

    doc = _build_purchase_doc(user_id, extracted, capture_method="screenshot")

    # Deduplication — uses order_date FROM RECEIPT
    if _check_dedup(db, user_id, doc):
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    # Unconfirmed date — ask user to confirm
    if doc["order_date_confidence"] == "estimated":
        return {
            "status": "date_unconfirmed",
            "message": "Couldn't read the order date. We've used yesterday as the purchase date. Is that correct?",
            "actions": ["confirm", "pick_date"],
            "preview": {k: v for k, v in extracted.items() if k != "raw_extracted_text"},
        }

    try:
        result = db.purchases.insert_one(doc)
    except Exception:
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    safe_doc = _serialize_purchase({**doc, "_id": result.inserted_id})
    return {"status": "saved", "purchase": safe_doc}


# ── Multi-screenshot upload ───────────────────────────────────────────────────

@router.post("/screenshot-multi")
async def upload_multiple_screenshots(
    file_0: Optional[UploadFile] = File(None),
    file_1: Optional[UploadFile] = File(None),
    file_2: Optional[UploadFile] = File(None),
    file_count: int = Form(...),
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    if file_count < 1 or file_count > 3:
        raise HTTPException(status_code=400, detail="file_count must be between 1 and 3")

    raw_files = [file_0, file_1, file_2][:file_count]
    images: list[bytes] = []
    mime_types: list[str] = []

    for f in raw_files:
        if f is None:
            raise HTTPException(status_code=400, detail="Expected file missing")
        if f.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images accepted")
        data = await f.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5MB.")
        images.append(data)
        mime_types.append(f.content_type or "image/jpeg")

    extracted = await extract_from_multiple_screenshots(images, mime_types)

    if extracted.get("error"):
        return {
            "status": "extraction_failed",
            "message": "Couldn't read these images. Try clearer screenshots or add manually.",
        }

    doc = _build_purchase_doc(user_id, extracted, capture_method="screenshot_multi")

    if _check_dedup(db, user_id, doc):
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    if doc["order_date_confidence"] == "estimated":
        return {
            "status": "date_unconfirmed",
            "message": "Couldn't read the order date. We've used yesterday as the purchase date. Is that correct?",
            "actions": ["confirm", "pick_date"],
            "preview": {k: v for k, v in extracted.items() if k != "raw_extracted_text"},
        }

    try:
        result = db.purchases.insert_one(doc)
    except Exception:
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    safe_doc = _serialize_purchase({**doc, "_id": result.inserted_id})
    return {"status": "success", "purchase": safe_doc}


# ── Confirm date (after unconfirmed screenshot) ───────────────────────────────

@router.post("/confirm-date")
async def confirm_date(
    payload: dict,
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    temp_data = payload.get("temp_purchase_data", {})
    action = payload.get("action", "confirm")
    confirmed_date_str = payload.get("confirmed_date")

    if action == "pick_date" and confirmed_date_str:
        temp_data["order_date"] = confirmed_date_str
        temp_data["order_date_confidence"] = "null"
    else:
        temp_data["order_date_confidence"] = "estimated"

    doc = _build_purchase_doc(user_id, temp_data, capture_method="screenshot")

    if _check_dedup(db, user_id, doc):
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    try:
        result = db.purchases.insert_one(doc)
    except Exception:
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    return {"status": "saved", "purchase_id": str(result.inserted_id)}


# ── Manual entry ──────────────────────────────────────────────────────────────

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

    existing = db.purchases.find_one({
        "user_id": ObjectId(user_id),
        "item_name": payload.item_name,
        "platform": payload.platform,
        "amount": payload.amount,
        "order_date": order_date,
    })
    if existing:
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    try:
        result = db.purchases.insert_one({
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
        })
    except Exception:
        return {"status": "already_logged", "message": "This purchase is already in your history ✓"}

    return {"status": "saved", "purchase_id": str(result.inserted_id)}


# ── Shop check ────────────────────────────────────────────────────────────────

@router.post("/check")
async def pre_purchase_check(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images accepted")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 5MB.")

    mime = file.content_type or "image/jpeg"
    product = await extract_product_for_check(image_bytes, mime_type=mime)

    if product.get("error") or not product.get("item_description"):
        return {
            "is_clear": True,
            "message": "Could not analyse image — screenshot is unclear",
            "item_checked": None,
        }

    # Fetch recent non-consumable purchases (last 60 days)
    sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
    cursor = db.purchases.find(
        {"user_id": ObjectId(user_id), "order_date": {"$gte": sixty_days_ago}, "is_consumable": False},
        {"item_name": 1, "platform": 1, "amount": 1, "order_date": 1},
    )
    recent = []
    for doc in cursor:
        recent.append({
            "item_name": doc["item_name"],
            "platform": doc.get("platform", ""),
            "amount": doc.get("amount", 0),
            "order_date": doc["order_date"].strftime("%Y-%m-%d") if doc.get("order_date") else "",
        })

    dup_result = await check_duplicate_purchase(product["item_description"], recent)

    bq_client = get_bigquery_client()
    wallet = await get_full_wallet_state(user_id, db, bq_client)
    spend_pct = wallet["spend_pct"]
    category_pcts = wallet.get("category_pcts", {})
    cat_key = _map_product_category(product.get("category", "other"))
    category_pct = category_pcts.get(cat_key, 0.0)

    is_duplicate = dup_result.get("is_duplicate", False)
    return {
        "is_clear": not is_duplicate,
        "similar_item": dup_result.get("matched_item"),
        "days_since": dup_result.get("days_since"),
        "confidence": dup_result.get("confidence", "unknown"),
        "nudge_needed": is_duplicate or spend_pct > 70,
        "spend_pct": spend_pct,
        "category_pct": category_pct,
        "item_checked": product.get("item_description"),
    }


def _map_product_category(gemini_cat: str) -> str:
    return {
        "clothing": "shopping_fashion",
        "electronics": "electronics_tech",
        "food": "food_dining_delivery",
        "health": "health_lifestyle",
        "entertainment": "entertainment_subs",
    }.get(gemini_cat, "others")


# ── Purchase history ──────────────────────────────────────────────────────────

@router.get("/history")
async def purchase_history(user_id: str = Depends(get_current_user)):
    db = get_db()
    if db is None:
        return {"purchases": []}

    sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=60)
    cursor = db.purchases.find(
        {"user_id": ObjectId(user_id), "order_date": {"$gte": sixty_days_ago}},
        sort=[("order_date", -1)],
    )
    return {"purchases": [_serialize_purchase(doc) for doc in cursor]}
