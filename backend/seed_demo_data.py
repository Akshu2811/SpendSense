"""
Run: python seed_demo_data.py
Seeds realistic demo data for user akki_test to demonstrate the full
SpendSense demo path: wallet in amber/aware state, fashion budget at 78%,
recent Blue Kurta purchase, past nudges with mixed responses.
"""
import os
import urllib.parse
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

_uri = os.getenv("MONGODB_URI", "")
_password = os.getenv("MONGODB_PASSWORD", "")
if _password and any(c in _password for c in "@#%&+"):
    _uri = _uri.replace(_password, urllib.parse.quote_plus(_password))

DB_NAME = os.getenv("MONGODB_DB_NAME", "spendsense")
client = MongoClient(_uri, serverSelectionTimeoutMS=8000)
db = client[DB_NAME]

now = datetime.now(timezone.utc)


def days_ago(n: int) -> datetime:
    return (now - timedelta(days=n)).replace(hour=10, minute=0, second=0, microsecond=0)


# ── Get or create akki_test user ──────────────────────────────────────────────
user = db.users.find_one({"username": "akki_test"})
if not user:
    result = db.users.insert_one({
        "username": "akki_test",
        "password_hash": bcrypt.hashpw(b"test1234", bcrypt.gensalt()).decode(),
        "created_at": now,
        "onboarding_complete": True,
    })
    user_id = result.inserted_id
    print("Created akki_test user:", user_id)
else:
    user_id = user["_id"]
    print("Found akki_test user:", user_id)

# ── Update user budget + wallet state ─────────────────────────────────────────
db.users.update_one(
    {"_id": user_id},
    {"$set": {
        "onboarding_complete": True,
        "budget.master_monthly": 15000,
        "budget.categories.food_dining_delivery": 4000,
        "budget.categories.shopping_fashion": 3000,
        "budget.categories.electronics_tech": 3000,
        "budget.categories.entertainment_subs": 1500,
        "budget.categories.health_lifestyle": 1500,
        "budget.categories.others": 2000,
        "budget.month_set": now.strftime("%Y-%m"),
        # Set wallet state so /wallet-state returns cached "aware" state (BigQuery offline)
        "wallet_state.current": "aware",
        "wallet_state.spend_pct": 58.0,
        "wallet_state.last_calculated": now,
        "wallet_state.state_since": now,
        "streak.current_days": 4,
        "streak.best_days": 7,
        "streak.last_updated": now,
        "data_connections.sync_method": "google_sheets",
        "preferences.notification_time": "09:00",
        "preferences.timezone": "Asia/Kolkata",
    }},
)
print("Updated akki_test budget + wallet state: aware, 58%")

# ── Clear old demo purchases for this user ────────────────────────────────────
db.purchases.delete_many({"user_id": user_id})
print("Cleared old purchases for akki_test")

# ── Seed purchases ────────────────────────────────────────────────────────────
purchases = [
    # Fashion (non-consumable) — the impulse category
    {"item_name": "Blue Printed Kurta", "platform": "Myntra", "amount": 899,
     "category": "shopping_fashion", "is_consumable": False, "order_date": days_ago(12)},
    {"item_name": "Floral Ethnic Top", "platform": "Ajio", "amount": 1200,
     "category": "shopping_fashion", "is_consumable": False, "order_date": days_ago(28)},
    {"item_name": "Pearl Earrings Set", "platform": "Myntra", "amount": 399,
     "category": "shopping_fashion", "is_consumable": False, "order_date": days_ago(35)},
    {"item_name": "Silk Scrunchie 3-Pack", "platform": "Nykaa", "amount": 249,
     "category": "shopping_fashion", "is_consumable": False, "order_date": days_ago(40)},

    # Food & Delivery (consumable)
    {"item_name": "Vegetables Mix Pack", "platform": "Zepto", "amount": 340,
     "category": "food_dining_delivery", "is_consumable": True, "order_date": days_ago(1)},
    {"item_name": "Biryani Order", "platform": "Swiggy", "amount": 320,
     "category": "food_dining_delivery", "is_consumable": True, "order_date": days_ago(3)},
    {"item_name": "Zomato Dinner", "platform": "Zomato", "amount": 450,
     "category": "food_dining_delivery", "is_consumable": True, "order_date": days_ago(5)},
    {"item_name": "Blinkit Grocery Run", "platform": "Blinkit", "amount": 680,
     "category": "food_dining_delivery", "is_consumable": True, "order_date": days_ago(8)},

    # Electronics (non-consumable)
    {"item_name": "Wireless Earbuds", "platform": "Amazon", "amount": 1299,
     "category": "electronics_tech", "is_consumable": False, "order_date": days_ago(45)},
    {"item_name": "Phone Case Clear", "platform": "Flipkart", "amount": 299,
     "category": "electronics_tech", "is_consumable": False, "order_date": days_ago(20)},

    # Entertainment (consumable - subscriptions)
    {"item_name": "Netflix Subscription", "platform": "Netflix", "amount": 649,
     "category": "entertainment_subs", "is_consumable": True, "order_date": days_ago(1)},
    {"item_name": "Spotify Premium", "platform": "Spotify", "amount": 119,
     "category": "entertainment_subs", "is_consumable": True, "order_date": days_ago(7)},

    # Health & Lifestyle (non-consumable)
    {"item_name": "Moisturiser SPF 50", "platform": "Nykaa", "amount": 599,
     "category": "health_lifestyle", "is_consumable": False, "order_date": days_ago(15)},
    {"item_name": "Yoga Mat 6mm", "platform": "Amazon", "amount": 799,
     "category": "health_lifestyle", "is_consumable": False, "order_date": days_ago(50)},

    # Others
    {"item_name": "Bookstore Order", "platform": "Amazon", "amount": 450,
     "category": "others", "is_consumable": False, "order_date": days_ago(22)},
]

inserted_count = 0
for p in purchases:
    doc = {
        "user_id": user_id,
        "item_name": p["item_name"],
        "item_description": p["item_name"],
        "platform": p["platform"],
        "amount": p["amount"],
        "category": p["category"],
        "subcategory": None,
        "order_date": p["order_date"],
        "capture_date": p["order_date"],
        "capture_method": "manual",
        "raw_extracted_text": None,
        "gemini_tags": [],
        "embedding_summary": None,
        "is_consumable": p["is_consumable"],
        "order_date_confidence": "confirmed",
    }
    try:
        db.purchases.insert_one(doc)
        inserted_count += 1
        print(f"  ✓ purchase: {p['item_name']} ({p['platform']}, ₹{p['amount']})")
    except Exception as e:
        print(f"  ✗ skip duplicate: {p['item_name']} — {e}")

print(f"Inserted {inserted_count}/{len(purchases)} purchases")

# ── Seed past nudges ──────────────────────────────────────────────────────────
db.nudges.delete_many({"user_id": user_id})
print("Cleared old nudges for akki_test")

nudges = [
    # Paused nudges (good responses)
    {"tier": "medium", "trigger_type": "pre_shop_check", "platform": "Myntra",
     "wallet_state_at_fire": "aware", "spend_pct_at_fire": 55.0,
     "user_response": "paused", "fired_at": days_ago(10),
     "gemini_copy": {"title": "your wardrobe called", "body": "already bought something from Myntra 3 weeks ago.", "tag": "fashion check 👀"}},
    {"tier": "light", "trigger_type": "morning_alert", "platform": None,
     "wallet_state_at_fire": "calm", "spend_pct_at_fire": 30.0,
     "user_response": "paused", "fired_at": days_ago(8),
     "gemini_copy": {"title": "good morning, financially stable human", "body": "30% used. you're doing great so far.", "tag": "morning check 💙"}},
    {"tier": "medium", "trigger_type": "pre_shop_check", "platform": "Amazon",
     "wallet_state_at_fire": "aware", "spend_pct_at_fire": 48.0,
     "user_response": "paused", "fired_at": days_ago(6),
     "gemini_copy": {"title": "earbuds again? really?", "body": "you bought wireless earbuds just 25 days ago bestie.", "tag": "duplicate check 👀"}},
    {"tier": "light", "trigger_type": "pre_shop_check", "platform": "Zepto",
     "wallet_state_at_fire": "aware", "spend_pct_at_fire": 52.0,
     "user_response": "paused", "fired_at": days_ago(4),
     "gemini_copy": {"title": "hold on", "body": "52% budget used. grocery run or impulse buy?", "tag": "quick check 💙"}},

    # Overridden nudges (they spent anyway)
    {"tier": "light", "trigger_type": "pre_shop_check", "platform": "Swiggy",
     "wallet_state_at_fire": "calm", "spend_pct_at_fire": 25.0,
     "user_response": "overridden", "fired_at": days_ago(9),
     "gemini_copy": {"title": "hunger is valid", "body": "25% used, you're within budget actually.", "tag": "all good 💙"}},
    {"tier": "medium", "trigger_type": "pre_shop_check", "platform": "Ajio",
     "wallet_state_at_fire": "aware", "spend_pct_at_fire": 44.0,
     "user_response": "overridden", "fired_at": days_ago(7),
     "gemini_copy": {"title": "going to ajio? bold", "body": "fashion budget at 60%. proceed with caution.", "tag": "heads up 👀"}},
    {"tier": "hard", "trigger_type": "pre_shop_check", "platform": "Myntra",
     "wallet_state_at_fire": "urgent", "spend_pct_at_fire": 76.0,
     "user_response": "overridden", "fired_at": days_ago(5),
     "gemini_copy": {"title": "bestie no", "body": "76% gone. fashion at 90%. do you really need this?", "tag": "urgent 🌶️"}},

    # Pending (most recent — from today)
    {"tier": "medium", "trigger_type": "morning_alert", "platform": None,
     "wallet_state_at_fire": "aware", "spend_pct_at_fire": 58.0,
     "user_response": "pending", "fired_at": now,
     "gemini_copy": {"title": "morning budget check", "body": "58% used with half the month left. solid.", "tag": "morning 👀"}},
]

nudge_ids = []
for n in nudges:
    responded_at = n["fired_at"] + timedelta(minutes=5) if n["user_response"] != "pending" else None
    doc = {
        "user_id": user_id,
        "fired_at": n["fired_at"],
        "tier": n["tier"],
        "trigger_type": n["trigger_type"],
        "wallet_state_at_fire": n["wallet_state_at_fire"],
        "spend_pct_at_fire": n["spend_pct_at_fire"],
        "context": {
            "platform": n.get("platform"),
            "similar_item": None,
            "similar_item_order_date": None,
            "days_since_similar": None,
            "category_pct": n["spend_pct_at_fire"],
            "master_pct": n["spend_pct_at_fire"],
        },
        "gemini_copy": n["gemini_copy"],
        "user_response": n["user_response"],
        "responded_at": responded_at,
        "transaction_followed": n["user_response"] == "overridden",
        "amount_after_nudge": None,
    }
    result = db.nudges.insert_one(doc)
    nudge_ids.append(result.inserted_id)
    print(f"  ✓ nudge: [{n['tier']}] {n['trigger_type']} → {n['user_response']}")

print(f"Inserted {len(nudge_ids)} nudges")

# ── Final summary ─────────────────────────────────────────────────────────────
print("\n══════════════════════════════")
print("DEMO DATA SEEDED SUCCESSFULLY")
print("══════════════════════════════")
print(f"User:        akki_test / test1234")
print(f"Budget:      ₹15,000/month")
print(f"Wallet:      aware (58%)")
print(f"Streak:      4 days current / 7 days best")
print(f"Purchases:   {inserted_count} items")
print(f"Nudges:      {len(nudge_ids)} total (4 paused, 3 overridden, 1 pending)")
print(f"Key item:    Blue Printed Kurta — Myntra — 12 days ago")
print("══════════════════════════════")
