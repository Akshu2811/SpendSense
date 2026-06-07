import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from db.bigquery import get_bigquery_client
from db.mongodb import get_db
from middleware.security import limiter
from models.schemas import WalletStateResponse
from routers.auth import get_current_user
from services.analysis_service import get_full_wallet_state
from services.bigquery_service import get_category_breakdown

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
