import os
from collections import Counter
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends

from db.mongodb import get_db
from models.schemas import MonthlyReportResponse
from routers.auth import get_current_user
from services.bigquery_service import get_monthly_total, get_category_breakdown

router = APIRouter(prefix="/report", tags=["reports"])

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")

EMPTY_CATEGORIES = {
    "food_dining_delivery": 0.0,
    "shopping_fashion": 0.0,
    "electronics_tech": 0.0,
    "entertainment_subs": 0.0,
    "health_lifestyle": 0.0,
    "others": 0.0,
}


@router.get("/current-month", response_model=MonthlyReportResponse)
async def current_month_report(user_id: str = Depends(get_current_user)):
    db = get_db()
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_date = month_start.date()

    # ── BigQuery: budget data ─────────────────────────────────────────────────
    total_spent = await get_monthly_total(GCP_PROJECT_ID, month_start_date)
    category_totals = await get_category_breakdown(GCP_PROJECT_ID, month_start_date)

    # ── MongoDB: user settings ────────────────────────────────────────────────
    master_budget = 15000.0
    categories_budget: dict = {}
    streak_data: dict = {"current_days": 0, "best_days": 0}

    if db is not None:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            master_budget = float(user.get("budget", {}).get("master_monthly", 15000) or 15000)
            categories_budget = {
                k: float(v)
                for k, v in (user.get("budget", {}).get("categories") or {}).items()
                if v is not None
            }
            streak_data = user.get("streak", streak_data)

    default_cat = master_budget / 6 if master_budget > 0 else 1
    utilisation_pct = round((total_spent / master_budget * 100), 2) if master_budget > 0 else 0.0
    category_breakdown = {
        cat: {
            "budget": categories_budget.get(cat, default_cat),
            "spent": category_totals.get(cat, 0.0),
            "pct": round(
                category_totals.get(cat, 0.0) / (categories_budget.get(cat) or default_cat) * 100, 2
            ),
        }
        for cat in EMPTY_CATEGORIES
    }

    # ── MongoDB: nudge stats ──────────────────────────────────────────────────
    nudge_summary = {
        "total_fired": 0, "total_paused": 0, "total_overridden": 0,
        "pause_rate_pct": 0.0, "estimated_saved": 0.0,
    }
    top_category = "others"
    top_platform = "unknown"
    nudge_count_by_category: dict = {}

    if db is not None:
        base_filter = {"user_id": ObjectId(user_id), "fired_at": {"$gte": month_start}}

        total_fired = db.nudges.count_documents(base_filter)
        total_paused = db.nudges.count_documents({**base_filter, "user_response": "paused"})
        total_overridden = db.nudges.count_documents({**base_filter, "user_response": "overridden"})
        pause_rate = round((total_paused / total_fired * 100), 2) if total_fired > 0 else 0.0

        # Estimated saved = sum amount_after_nudge on paused nudges
        # If not set, fall back to avg purchase * paused count
        paused_cursor = db.nudges.find(
            {**base_filter, "user_response": "paused"},
            {"amount_after_nudge": 1, "context.master_pct": 1},
        )
        saved_amounts = [
            float(n["amount_after_nudge"])
            for n in paused_cursor
            if n.get("amount_after_nudge") is not None
        ]
        if saved_amounts:
            estimated_saved = sum(saved_amounts)
        else:
            # Rough estimate: paused nudges × avg purchase amount
            purchases_this_month = db.purchases.find(
                {"user_id": ObjectId(user_id), "order_date": {"$gte": month_start}}
            )
            amounts = [p.get("amount", 0) for p in purchases_this_month]
            avg_purchase = (sum(amounts) / len(amounts)) if amounts else 800.0
            estimated_saved = round(avg_purchase * total_paused, 2)

        # Top category by purchase count
        purchases_cursor = db.purchases.find(
            {"user_id": ObjectId(user_id), "order_date": {"$gte": month_start}},
            {"category": 1},
        )
        cat_counts = Counter(p.get("category", "others") for p in purchases_cursor)
        if cat_counts:
            top_category = cat_counts.most_common(1)[0][0]
        nudge_count_by_category = dict(cat_counts)

        # Top platform
        platform_cursor = db.nudges.find(base_filter, {"context.platform": 1})
        platform_counts = Counter(
            n.get("context", {}).get("platform") for n in platform_cursor
            if n.get("context", {}).get("platform")
        )
        if platform_counts:
            top_platform = platform_counts.most_common(1)[0][0]

        nudge_summary = {
            "total_fired": total_fired,
            "total_paused": total_paused,
            "total_overridden": total_overridden,
            "pause_rate_pct": pause_rate,
            "estimated_saved": round(estimated_saved, 2),
        }

    # ── Upsert to monthly_reports ─────────────────────────────────────────────
    report_doc = {
        "user_id": ObjectId(user_id),
        "month": month_str,
        "generated_at": now,
        "budget_summary": {
            "master_budget": master_budget,
            "total_spent": total_spent,
            "utilisation_pct": utilisation_pct,
            "category_breakdown": category_breakdown,
        },
        "nudge_summary": nudge_summary,
        "streak_summary": {
            "best_streak_days": streak_data.get("best_days", 0),
            "final_streak_days": streak_data.get("current_days", 0),
        },
        "insights": {
            "top_impulse_category": top_category,
            "top_impulse_platform": top_platform,
            "nudge_count_by_category": nudge_count_by_category,
            "gemini_insight_text": "Keep tracking your purchases for personalised insights.",
        },
        "wallet_state_distribution": {"days_calm": 0, "days_aware": 0, "days_urgent": 0, "days_crisis": 0},
    }

    if db is not None:
        db.monthly_reports.update_one(
            {"user_id": ObjectId(user_id), "month": month_str},
            {"$set": report_doc},
            upsert=True,
        )

    return MonthlyReportResponse(
        month=month_str,
        budget_summary=report_doc["budget_summary"],
        nudge_summary=nudge_summary,
        streak_summary=report_doc["streak_summary"],
        insights=report_doc["insights"],
    )
