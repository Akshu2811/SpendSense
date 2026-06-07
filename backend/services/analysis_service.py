import logging
import os
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")

EMPTY_CATEGORIES: dict = {
    "food_dining_delivery": 0.0,
    "shopping_fashion": 0.0,
    "electronics_tech": 0.0,
    "entertainment_subs": 0.0,
    "health_lifestyle": 0.0,
    "others": 0.0,
}


def calculate_wallet_state(spend_pct: float) -> str:
    if spend_pct < 40:
        return "calm"
    if spend_pct < 70:
        return "aware"
    if spend_pct < 85:
        return "urgent"
    return "crisis"


def calculate_nudge_tier(budget_pct: float, has_similar_item: bool) -> str:
    if budget_pct > 85 and has_similar_item:
        return "hard"
    if budget_pct > 70 or has_similar_item:
        return "medium"
    return "light"


async def get_full_wallet_state(user_id, db, bq_client) -> dict:
    from services.bigquery_service import get_monthly_total, get_category_breakdown  # noqa: PLC0415

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()

    # Fetch user from MongoDB
    user = None
    master_monthly = 15000.0
    cached_state = None
    last_calculated = None
    category_budgets = {}

    if db is not None:
        from bson import ObjectId  # noqa: PLC0415

        user = db.users.find_one({"_id": ObjectId(str(user_id))})

    if user:
        master_monthly = float(user.get("budget", {}).get("master_monthly", 15000) or 15000)
        cached_state = user.get("wallet_state", {})
        last_calculated = cached_state.get("last_calculated") if cached_state else None
        cat_budgets = user.get("budget", {}).get("categories") or {}
        category_budgets = {k: float(v) for k, v in cat_budgets.items() if v is not None}

    # Query BigQuery for total spend
    total_spent = await get_monthly_total(GCP_PROJECT_ID, month_start)

    # If BigQuery returned 0 and cache is fresh (within 1 hour), return stale cache
    if total_spent == 0.0 and last_calculated is not None:
        cache_age = now - (
            last_calculated if last_calculated.tzinfo else last_calculated.replace(tzinfo=timezone.utc)
        )
        if cache_age < timedelta(hours=1) and cached_state:
            return {
                "state": cached_state.get("current", "calm"),
                "spend_pct": float(cached_state.get("spend_pct", 0)),
                "category_pcts": dict(EMPTY_CATEGORIES),
                "last_updated": last_calculated,
                "stale": True,
            }

    spend_pct = (total_spent / master_monthly * 100) if master_monthly > 0 else 0.0
    category_totals = await get_category_breakdown(GCP_PROJECT_ID, month_start)

    # Calculate per-category %
    default_cat_budget = master_monthly / 6
    category_pcts: dict = {}
    for cat in EMPTY_CATEGORIES:
        cat_budget = category_budgets.get(cat, default_cat_budget) or default_cat_budget
        cat_spent = category_totals.get(cat, 0.0)
        category_pcts[cat] = round((cat_spent / cat_budget * 100) if cat_budget > 0 else 0.0, 2)

    state = calculate_wallet_state(spend_pct)

    # Persist to MongoDB
    if db is not None and user is not None:
        from bson import ObjectId  # noqa: PLC0415

        db.users.update_one(
            {"_id": ObjectId(str(user_id))},
            {
                "$set": {
                    "wallet_state.current": state,
                    "wallet_state.spend_pct": round(spend_pct, 2),
                    "wallet_state.last_calculated": now,
                }
            },
        )

    return {
        "state": state,
        "spend_pct": round(spend_pct, 2),
        "category_pcts": category_pcts,
        "last_updated": now,
        "stale": False,
    }
