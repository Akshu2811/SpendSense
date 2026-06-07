import bcrypt
import logging
import os
import urllib.parse
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure

load_dotenv()

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db = None


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def get_db():
    return _db


def is_connected() -> bool:
    return _db is not None


def _safe_uri(uri: str) -> str:
    """URL-encode the password in a MongoDB URI if it contains special characters."""
    password = os.getenv("MONGODB_PASSWORD", "")
    if not password or not any(c in password for c in "@#%&+"):
        return uri
    encoded = urllib.parse.quote_plus(password)
    return uri.replace(password, encoded)


def init_db() -> None:
    global _client, _db

    uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("MONGODB_DB_NAME", "spendsense")

    if not uri or "placeholder" in uri.lower():
        logger.warning("MongoDB not connected — running in offline mode")
        return

    uri = _safe_uri(uri)

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[db_name]
        logger.info("MongoDB connected: %s", db_name)
        _create_indexes()
        _seed_test_user()
    except (ConnectionFailure, OperationFailure, Exception) as exc:
        logger.warning("MongoDB not connected — running in offline mode: %s", exc)
        _client = None
        _db = None


def _create_indexes() -> None:
    if _db is None:
        return

    # users
    _db.users.create_index([("username", ASCENDING)], unique=True)
    _db.users.create_index([("wallet_state.current", ASCENDING)])

    # purchases — unique compound prevents duplicate purchases
    _db.purchases.create_index(
        [("user_id", ASCENDING), ("order_date", DESCENDING)]
    )
    _db.purchases.create_index(
        [("user_id", ASCENDING), ("platform", ASCENDING)]
    )
    _db.purchases.create_index(
        [("user_id", ASCENDING), ("is_consumable", ASCENDING)]
    )
    _db.purchases.create_index(
        [
            ("user_id", ASCENDING),
            ("item_name", ASCENDING),
            ("platform", ASCENDING),
            ("amount", ASCENDING),
            ("order_date", ASCENDING),
        ],
        unique=True,
    )

    # nudges
    _db.nudges.create_index(
        [("user_id", ASCENDING), ("fired_at", DESCENDING)]
    )
    _db.nudges.create_index(
        [("user_id", ASCENDING), ("user_response", ASCENDING)]
    )

    # monthly_reports
    _db.monthly_reports.create_index(
        [("user_id", ASCENDING), ("month", ASCENDING)]
    )

    logger.info("MongoDB indexes created")


def _seed_test_user() -> None:
    if _db is None:
        return

    if _db.users.find_one({"username": "akki_test"}):
        return

    now = datetime.now(timezone.utc)
    _db.users.insert_one(
        {
            "username": "akki_test",
            "password_hash": _hash_password("test1234"),
            "created_at": now,
            "onboarding_complete": False,
            "budget": {
                "master_monthly": 15000,
                "categories": {
                    "food_dining_delivery": None,
                    "shopping_fashion": None,
                    "electronics_tech": None,
                    "entertainment_subs": None,
                    "health_lifestyle": None,
                    "others": None,
                },
                "month_set": now.strftime("%Y-%m"),
            },
            "wallet_state": {
                "current": "calm",
                "spend_pct": 0,
                "last_calculated": None,
                "state_since": now,
            },
            "streak": {
                "current_days": 0,
                "best_days": 0,
                "last_updated": now,
            },
            "data_connections": {
                "fivetran_connector_id": None,
                "last_sync": None,
                "sync_method": "manual",
            },
            "preferences": {
                "notification_time": "09:00",
                "timezone": "Asia/Kolkata",
            },
        }
    )
    logger.info("Seeded test user: akki_test")
