import os

import httpx

try:
    from google.adk.tools import tool as adk_tool
    _HAS_ADK = True
except ImportError:
    _HAS_ADK = False
    def adk_tool(fn):
        return fn

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


@adk_tool
def get_wallet_state(user_token: str) -> dict:
    """Gets the current wallet state for a user including spend percentage
    and category breakdown. Returns state (calm/aware/urgent/crisis),
    spend_pct, and category_pcts."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/wallet-state",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=10.0,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e), "state": "unknown", "spend_pct": 0}


@adk_tool
def fire_nudge(
    user_token: str,
    trigger_type: str,
    platform: str = None,
    context: dict = None,
) -> dict:
    """Fires a behavioral nudge for the user. trigger_type must be one of:
    pre_shop_check, morning_alert, budget_breach, frequency_pattern.
    Returns the nudge payload with title, body, tier."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/nudges/fire",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "trigger_type": trigger_type,
                "platform": platform,
                "context": context or {},
            },
            timeout=10.0,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@adk_tool
def get_purchase_history(user_token: str) -> dict:
    """Gets the user's last 60 days of non-consumable purchase history
    from MongoDB. Used for duplicate/impulse detection."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/purchases/history",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=10.0,
        )
        return {"purchases": response.json()}
    except Exception as e:
        return {"error": str(e), "purchases": []}


@adk_tool
def sync_transactions(user_token: str) -> dict:
    """Triggers a Fivetran MCP sync to pull latest transactions
    from Google Sheets into BigQuery. Call this before analysing
    spending to ensure data is fresh."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/transactions/sync",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=30.0,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "sync_failed"}


@adk_tool
def get_monthly_report(user_token: str) -> dict:
    """Gets the current month spending report including nudges fired,
    pause rate, estimated savings, and category breakdown."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/report/current-month",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=10.0,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}
