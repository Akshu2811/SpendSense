import logging
import os
import sys

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.auth import get_current_user
from jose import JWTError, jwt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "agent"))

try:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("spendsense_agent_main", os.path.join(_agent_dir, "main.py"),
        submodule_search_locations=[_agent_dir])
    _agent_main = _ilu.module_from_spec(_spec)
    # Add agent dir to path so spendsense_agent package resolves inside agent/main.py
    if _agent_dir not in sys.path:
        sys.path.insert(0, _agent_dir)
    _spec.loader.exec_module(_agent_main)
    run_morning_check = _agent_main.run_morning_check
    run_pre_shop_check = _agent_main.run_pre_shop_check
    _ADK_RUNNER_READY = _agent_main._ADK_RUNNER_READY
    _ADK_IMPORT_OK = True
    logger.info("ADK agent loaded from %s (runner_ready=%s)", _agent_dir, _ADK_RUNNER_READY)
except Exception as e:
    logger.warning("ADK agent import failed (%s) — fallback mode active", e)
    _ADK_IMPORT_OK = False
    _ADK_RUNNER_READY = False


def _token_for_user(user_id: str) -> str:
    """Re-encode the user_id into a short-lived JWT for internal ADK calls."""
    from datetime import datetime, timezone, timedelta
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def _fallback_morning_check(user_id: str, user_token: str) -> dict:
    """Direct Gemini call when ADK is unavailable."""
    try:
        from services.gemini_service import generate_morning_copy
        from db.mongodb import get_db
        from db.bigquery import get_bigquery_client
        from services.analysis_service import get_full_wallet_state
        from bson import ObjectId

        db = get_db()
        bq = get_bigquery_client()
        wallet = await get_full_wallet_state(user_id, db, bq)
        state = wallet.get("state", "calm")
        spend_pct = wallet.get("spend_pct", 0.0)

        last_platform = None
        days_since = None
        if db is not None:
            last_nudge = db.nudges.find_one(
                {"user_id": ObjectId(user_id)},
                sort=[("fired_at", -1)],
            )
            if last_nudge:
                last_platform = last_nudge.get("context", {}).get("platform")

        copy = await generate_morning_copy(state, spend_pct, last_platform, days_since)

        from services.gemini_service import generate_nudge_copy
        from services.analysis_service import calculate_nudge_tier
        from db.mongodb import get_db as _get_db
        from datetime import datetime, timezone
        from bson import ObjectId as ObjId

        tier = calculate_nudge_tier(spend_pct, False)
        nudge_copy = await generate_nudge_copy(
            state=state,
            spend_pct=spend_pct,
            platform=None,
            similar_item=None,
            days_since=None,
            category_pct=spend_pct,
        )

        _db = _get_db()
        if _db is not None:
            _db.nudges.insert_one({
                "user_id": ObjId(user_id),
                "fired_at": datetime.now(timezone.utc),
                "tier": tier,
                "trigger_type": "morning_alert",
                "wallet_state_at_fire": state,
                "spend_pct_at_fire": spend_pct,
                "context": {},
                "gemini_copy": nudge_copy,
                "user_response": "pending",
                "responded_at": None,
                "transaction_followed": None,
                "amount_after_nudge": None,
            })

        return {
            "status": "completed",
            "result": f"{copy.get('title', '')} — {copy.get('body', '')}",
            "nudge_fired": True,
            "mode": "fallback",
        }
    except Exception as exc:
        logger.error("Fallback morning check failed: %s", exc)
        return {"status": "completed", "result": "Morning check done", "nudge_fired": False, "mode": "fallback"}


async def _fallback_pre_shop_check(user_id: str, user_token: str, platform: str) -> dict:
    """Direct Gemini + nudge call when ADK is unavailable."""
    try:
        from db.mongodb import get_db
        from db.bigquery import get_bigquery_client
        from services.analysis_service import get_full_wallet_state, calculate_nudge_tier
        from services.gemini_service import generate_nudge_copy
        from bson import ObjectId
        from datetime import datetime, timezone

        db = get_db()
        bq = get_bigquery_client()
        wallet = await get_full_wallet_state(user_id, db, bq)
        state = wallet.get("state", "calm")
        spend_pct = wallet.get("spend_pct", 0.0)

        tier = calculate_nudge_tier(spend_pct, False)
        nudge_copy = await generate_nudge_copy(
            state=state,
            spend_pct=spend_pct,
            platform=platform,
            similar_item=None,
            days_since=None,
            category_pct=spend_pct,
        )

        nudge_fired = False
        if db is not None:
            db.nudges.insert_one({
                "user_id": ObjectId(user_id),
                "fired_at": datetime.now(timezone.utc),
                "tier": tier,
                "trigger_type": "pre_shop_check",
                "wallet_state_at_fire": state,
                "spend_pct_at_fire": spend_pct,
                "context": {"platform": platform},
                "gemini_copy": nudge_copy,
                "user_response": "pending",
                "responded_at": None,
                "transaction_followed": None,
                "amount_after_nudge": None,
            })
            nudge_fired = True

        return {
            "status": "completed",
            "nudge_fired": nudge_fired,
            "nudge": nudge_copy,
            "mode": "fallback",
        }
    except Exception as exc:
        logger.error("Fallback pre-shop check failed: %s", exc)
        return {"status": "completed", "nudge_fired": False, "mode": "fallback"}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/morning-check")
async def morning_check(user_id: str = Depends(get_current_user)):
    user_token = _token_for_user(user_id)

    if _ADK_IMPORT_OK and _ADK_RUNNER_READY:
        try:
            result = await run_morning_check(user_id, user_token)
            return {"status": "completed", "result": result, "mode": "adk"}
        except Exception as exc:
            logger.warning("ADK morning check failed, falling back: %s", exc)

    return await _fallback_morning_check(user_id, user_token)


class PreShopRequest(BaseModel):
    platform: str


@router.post("/pre-shop-check")
async def pre_shop_check(
    payload: PreShopRequest,
    user_id: str = Depends(get_current_user),
):
    user_token = _token_for_user(user_id)
    platform = payload.platform.strip()

    if _ADK_IMPORT_OK and _ADK_RUNNER_READY:
        try:
            result = await run_pre_shop_check(user_id, user_token, platform)
            return {"status": "completed", "result": result, "nudge_fired": True, "mode": "adk"}
        except Exception as exc:
            logger.warning("ADK pre-shop check failed, falling back: %s", exc)

    return await _fallback_pre_shop_check(user_id, user_token, platform)
