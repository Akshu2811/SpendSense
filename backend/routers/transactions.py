import io
import os
from datetime import datetime, timezone

import pandas as pd
from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from db.bigquery import get_bigquery_client
from db.mongodb import get_db
from middleware.security import limiter
from models.schemas import WalletStateResponse
from routers.auth import get_current_user
from services.analysis_service import get_full_wallet_state
from services.bigquery_service import get_category_breakdown

_CSV_COLUMN_ALIASES = {
    "date":           ["date", "transaction date", "txn date", "value date", "posting date", "trans date"],
    "merchant":       ["merchant", "description", "narration", "particulars", "details", "remarks", "beneficiary"],
    "amount":         ["amount", "debit", "withdrawal", "dr.", "debit amount", "amount (inr)", "transaction amount", "dr amount"],
    "category":       ["category", "type", "transaction type", "mcc category"],
    "payment_method": ["payment method", "mode", "payment mode", "instrument"],
}

_MERCHANT_CATEGORY_KEYWORDS = {
    "shopping_fashion":    ["myntra", "ajio", "nykaa", "meesho", "zara", "h&m", "fashion"],
    "food_dining_delivery": ["swiggy", "zomato", "zepto", "blinkit", "domino", "mcdonald", "kfc", "pizza"],
    "electronics_tech":    ["croma", "reliance digital", "apple store"],
    "entertainment_subs":  ["netflix", "spotify", "hotstar", "youtube", "prime", "jio cinema"],
    "health_lifestyle":    ["pharmacy", "chemist", "gym", "cult", "medplus", "apollo"],
}


def _infer_category(merchant: str) -> str:
    m = str(merchant).lower()
    for cat, keywords in _MERCHANT_CATEGORY_KEYWORDS.items():
        if any(kw in m for kw in keywords):
            return cat
    return "others"

router = APIRouter(tags=["transactions"])

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")


@router.get("/wallet-state", response_model=WalletStateResponse)
async def wallet_state(user_id: str = Depends(get_current_user)):
    db = get_db()
    bq_client = get_bigquery_client()
    result = await get_full_wallet_state(user_id, db, bq_client)
    return WalletStateResponse(**result)


@router.post("/transactions/sync")
@limiter.limit("2/minute")
async def sync_transactions(request: Request, user_id: str = Depends(get_current_user)):
    return {"status": "sync_triggered", "message": "Fivetran sync initiated"}


@router.get("/transactions/recent")
async def recent_transactions(user_id: str = Depends(get_current_user)):
    return {"transactions": [], "message": "Connect Fivetran to see transactions"}


@router.post("/transactions/upload-csv")
@limiter.limit("5/minute")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    contents = await file.read()

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    if not contents.strip():
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse file. Ensure it is a valid CSV.")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV has no data rows.")

    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map whatever column names the bank uses to our standard names
    col_map: dict[str, str] = {}
    for field, aliases in _CSV_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                col_map[field] = alias
                break

    missing = [f for f in ("date", "merchant", "amount") if f not in col_map]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Required columns not found: {missing}. "
                f"Columns in file: {list(df.columns)}. "
                "Expected: date/transaction date, merchant/description/narration, amount/debit."
            ),
        )

    df = df.rename(columns={v: k for k, v in col_map.items()})

    df["amount"] = pd.to_numeric(
        df["amount"].astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip(),
        errors="coerce",
    )
    df = df[df["amount"].notna() & (df["amount"] > 0)]

    if df.empty:
        raise HTTPException(status_code=400, detail="No valid transactions found — all rows had zero or invalid amounts.")

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
    df = df[df["date"].notna()]

    if "category" not in df.columns:
        df["category"] = df["merchant"].apply(_infer_category)

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["date", "merchant", "amount"])
    dupes_removed = before_dedup - len(df)

    count = len(df)
    if count == 0:
        raise HTTPException(status_code=400, detail="No valid transactions to import after cleaning.")

    db = get_db()
    now = datetime.now(timezone.utc)
    if db is not None:
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "data_connections.last_sync": now,
                "data_connections.last_import_count": count,
                "data_connections.last_import_at": now,
                "data_connections.sync_method": "csv_upload",
            }},
        )

    return {
        "status": "success",
        "transactions_imported": count,
        "duplicates_removed": dupes_removed,
        "message": f"Successfully imported {count} transactions.",
    }


@router.get("/transactions/summary")
async def transaction_summary(user_id: str = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).date()
    categories = await get_category_breakdown(GCP_PROJECT_ID, month_start)
    total = sum(categories.values())
    return {
        "categories": categories,
        "month": now.strftime("%Y-%m"),
        "total": total,
    }
