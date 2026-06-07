import os
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends

from db.bigquery import get_bigquery_client
from db.mongodb import get_db
from models.schemas import MonthlyReportResponse
from routers.auth import get_current_user
from services.bigquery_service import get_monthly_total, get_category_breakdown

router = APIRouter(prefix="/report", tags=["reports"])

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")


@router.get("/current-month", response_model=MonthlyReportResponse)
async def current_month_report(user_id: str = Depends(get_current_user)):
    db = get_db()
    now = datetime.now(timezone.utc)
    month_str = now.strftime("%Y-%m")
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_date = month_start.date()

    # Budget data from BigQuery
    total_spent = await get_monthly_total(GCP_PROJECT_ID, month_start_date)
    category_totals = await get_category_breakdown(GCP_PROJECT_ID, month_start_date)

    master_budget = 15000.0
    categories_budget: dict = {}
    streak_data = {"current_days": 0, "best_days": 0}

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

    utilisation_pct = round((total_spent / master_budget * 100), 2) if master_budget > 0 else 0.0
    default_cat = master_budget / 6 if master_budget > 0 else 1
    category_breakdown = {
        cat: {
            "budget": categories_budget.get(cat, default_cat),
            "spent": category_totals.get(cat, 0.0),
            "pct": round(category_totals.get(cat, 0.0) / (categories_budget.get(cat) or default_cat) * 100, 2),
        }
        for cat in category_totals
    }

    # Nudge stats from MongoDB
    nudge_summary = {"total_fired": 0, "total_paused": 0, "total_overridden": 0, "pause_rate_pct": 0, "estimated_saved": 0}
    top_category = "others"
    top_platform = "unknown"

    if db is not None:
        total_fired = db.nudges.count_documents(
            {"user_id": ObjectId(user_id), "fired_at": {"$gte": month_start}}
        )
        total_paused = db.nudges.count_documents(
            {"user_id": ObjectId(user_id), "fired_at": {"$gte": month_start}, "user_response": "paused"}
        )
        total_overridden = db.nudges.count_documents(
            {"user_id": ObjectId(user_id), "fired_at": {"$gte": month_start}, "user_response": "overridden"}
        )
        pause_rate = round((total_paused / total_fired * 100), 2) if total_fired > 0 else 0.0
        nudge_summary = {
            "total_fired": total_fired,
            "total_paused": total_paused,
            "total_overridden": total_overridden,
            "pause_rate_pct": pause_rate,
            "estimated_saved": 0,
        }

    return MonthlyReportResponse(
        month=month_str,
        budget_summary={
            "master_budget": master_budget,
            "total_spent": total_spent,
            "utilisation_pct": utilisation_pct,
            "category_breakdown": category_breakdown,
        },
        nudge_summary=nudge_summary,
        streak_summary={
            "best_streak_days": streak_data.get("best_days", 0),
            "final_streak_days": streak_data.get("current_days", 0),
        },
        insights={
            "top_impulse_category": top_category,
            "top_impulse_platform": top_platform,
            "nudge_count_by_category": {},
            "gemini_insight_text": "Connect Fivetran and add purchases to generate insights.",
        },
    )
