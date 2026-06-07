# Document 05 — Backend Schema
# SpendSense

---

## Database Provider

### BigQuery (GCP) — transaction data only
Project: spendsense-[id]
Dataset: spendsense_data
Table: google_sheets.transactions
Region: GCP us-central1
Filled by: Fivetran pipeline (Google Sheets → BigQuery)
Read by: FastAPI bigquery_service.py for budget calculations

### MongoDB Atlas — application data only
Tier: M0 free tier
Region: GCP asia-south1 (Mumbai)
Database: spendsense
Collections: users, purchases, nudges, monthly_reports
Filled by: FastAPI on user actions

---

## Core Design Principle — Two Stores, Two Purposes

```
BIGQUERY                         MONGODB
────────────────────────         ────────────────────
Source: Fivetran pipeline        Source: User actions via app
        Google Sheets sync

Powers: Budget % calculation     Powers: Impulse detection
        Wallet state             Duplicate item check
        Category spend totals    User auth + settings
        Spend frequency          Nudge history
                                 Monthly reports

Data:   merchant + amount        Data:   item_name + platform
        + date + category                + amount + order_date
        NO item details                  FULL item details

NEVER use BigQuery               NEVER use MongoDB
for impulse detection            for budget calculation

These two stores NEVER mix for any calculation.
```

---

## Deduplication Rules — Critical

### Rule 1 — BigQuery transactions (Fivetran imports)
Duplicate = same merchant + amount + transaction_date
Action: Fivetran handles this via transaction_id unique key
FastAPI double-checks before any manual insert

### Rule 2 — MongoDB purchases (screenshot/share/manual)
Duplicate = same user + item_name + platform + amount + order_date

IMPORTANT: order_date = date shown ON THE RECEIPT
extracted by Gemini Vision
NOT the date user uploaded to SpendSense

All four fields must match → duplicate → do not save
Any one field different → new purchase → save it

Examples:
```
Blue Kurta + Myntra + ₹899 + June 6     → saved ✓
Blue Kurta + Myntra + ₹899 + June 6     → DUPLICATE ✗
Blue Kurta + Myntra + ₹899 + June 7     → saved ✓ (diff date)
Floral Dress + Myntra + ₹1,500 + June 6 → saved ✓ (diff item)
Blue Kurta + Ajio + ₹899 + June 6       → saved ✓ (diff platform)
Blue Kurta + Myntra + ₹1,200 + June 6   → saved ✓ (diff amount)
```

Action on duplicate purchase:
- Do NOT save silently
- Notify user: "This purchase is already in your history ✓"

### Rule 3 — MongoDB unique indexes (safety net)
Even if application code misses a duplicate,
MongoDB rejects it at database level.

---

## Impulse Detection Rule

ONLY MongoDB purchases collection is used for impulse detection.
BigQuery transactions are NEVER used for impulse detection.

Why: BigQuery transactions have no item details — only ₹ amounts.
Gemini cannot detect "similar ethnic wear" from
"Myntra ₹899 2026-06-02"

Sources that feed impulse detection:
✓ Screenshot upload (Gemini Vision extracts item)
✓ Share button (Gemini extracts from shared content)
✓ Manual entry (user typed item details)
✗ Fivetran → BigQuery (no item details — excluded)

---

## BigQuery Table: google_sheets.transactions

Filled by Fivetran automatically from Google Sheets.
FastAPI reads this for all budget calculations.

```
Schema (matches Google Sheet columns):
transaction_id  STRING   (unique, prevents duplicate imports)
date            DATE     (YYYY-MM-DD)
merchant        STRING   (clean name: Zepto, Myntra etc.)
amount          FLOAT    (positive numbers only)
category        STRING   (food_dining_delivery|shopping_fashion|
                          electronics_tech|entertainment_subs|
                          health_lifestyle|others)
payment_method  STRING   (upi|credit_card|debit_card)
description     STRING   (optional note)
```

Key BigQuery queries FastAPI runs:
```sql
-- Total spent this month (wallet state calculation)
SELECT SUM(amount) as total
FROM `spendsense_data.google_sheets.transactions`
WHERE DATE(date) >= DATE_TRUNC(CURRENT_DATE(), MONTH)

-- Spend by category (dashboard breakdown)
SELECT category, SUM(amount) as total
FROM `spendsense_data.google_sheets.transactions`
WHERE DATE(date) >= DATE_TRUNC(CURRENT_DATE(), MONTH)
GROUP BY category

-- Transaction frequency (impulse pattern detection)
SELECT merchant, COUNT(*) as frequency
FROM `spendsense_data.google_sheets.transactions`
WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY merchant
ORDER BY frequency DESC
```

---

## MongoDB Collections Overview

| Collection | Purpose | Filled by |
|---|---|---|
| users | Auth + budget + wallet state | Registration + onboarding |
| purchases | Item-level purchase data | Screenshot/share/manual |
| nudges | Every nudge fired + response | Agent nudge engine |
| monthly_reports | Month-end summaries | Auto-generated |

Note: transactions collection does NOT exist in MongoDB.
All transaction data lives in BigQuery.

---

## MongoDB Collection 1: users

```json
{
  "_id": "ObjectId (auto)",
  "username": "string (unique, required)",
  "password_hash": "string (bcrypt, never plaintext)",
  "created_at": "ISODate",
  "onboarding_complete": "boolean (default: false)",

  "budget": {
    "master_monthly": "number (₹, required)",
    "categories": {
      "food_dining_delivery": "number (₹, optional)",
      "shopping_fashion": "number (₹, optional)",
      "electronics_tech": "number (₹, optional)",
      "entertainment_subs": "number (₹, optional)",
      "health_lifestyle": "number (₹, optional)",
      "others": "number (₹, optional)"
    },
    "month_set": "string (e.g. 2026-06)"
  },

  "wallet_state": {
    "current": "string (calm|aware|urgent|crisis)",
    "spend_pct": "number (0-100)",
    "last_calculated": "ISODate",
    "state_since": "ISODate"
  },

  "streak": {
    "current_days": "number (default: 0)",
    "best_days": "number (default: 0)",
    "last_updated": "ISODate"
  },

  "data_connections": {
    "fivetran_connector_id": "string (nullable)",
    "last_sync": "ISODate (nullable)",
    "sync_method": "string (google_sheets|manual)"
  },

  "preferences": {
    "notification_time": "string (default: 09:00)",
    "timezone": "string (default: Asia/Kolkata)"
  }
}
```

**Indexes:**
```
username             → unique index (fast login lookup)
wallet_state.current → index (dashboard load)
```

---

## MongoDB Collection 2: purchases

Powers: impulse detection, duplicate item check
Does NOT power: budget calculation, wallet state
Those come from BigQuery.

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",

  "item_name": "string (e.g. Blue Printed Kurta)",
  "item_description": "string (full extracted description)",
  "platform": "string (Myntra|Amazon|Flipkart|Zepto|
                        Blinkit|Swiggy|Ajio|Nykaa|Other)",
  "amount": "number (₹)",
  "category": "string (same enum as BigQuery)",
  "subcategory": "string (e.g. ethnic_wear, sneakers)",

  "order_date": "ISODate (date FROM receipt/confirmation
                           extracted by Gemini Vision
                           NOT the upload date)",
  "capture_date": "ISODate (when user uploaded to SpendSense
                             used for audit trail only
                             NEVER used for business logic)",

  "capture_method": "string (screenshot|share|manual)",
  "raw_extracted_text": "string (Gemini Vision raw output)",

  "gemini_tags": ["array of semantic tags for similarity"],
  "embedding_summary": "string (for Gemini similarity compare)",

  "is_consumable": "boolean (true = grocery/medicine/daily
                             false = clothing/electronics/
                                     lifestyle — these get
                                     checked for duplicates)",

  "order_date_confidence": "string (confirmed|estimated|null)
                             confirmed = Gemini read from receipt
                             estimated = used capture_date - 1 day
                             null = user manually corrected"
}
```

**Indexes:**
```
{ user_id, order_date }                          → compound
{ user_id, platform }                            → compound
{ user_id, is_consumable }                       → index
{ user_id, item_name, platform, amount,
  order_date }                                   → unique compound
```

**Deduplication check — uses order_date from receipt:**
```python
def is_duplicate_purchase(user_id, item_name,
                           platform, amount, order_date):
    existing = db.purchases.find_one({
        "user_id": user_id,
        "item_name": item_name,
        "platform": platform,
        "amount": amount,
        "order_date": order_date  # date FROM receipt
    })
    return existing is not None

if is_duplicate_purchase(...):
    return {
        "status": "already_logged",
        "message": "This purchase is already in your history ✓"
    }
else:
    db.purchases.insert_one(purchase)
```

**If order_date not found on receipt:**
```python
if gemini_order_date is None:
    estimated_date = capture_date - timedelta(days=1)
    order_date_confidence = "estimated"
    return {
        "status": "date_unconfirmed",
        "message": "Couldn't read the order date. "
                   "We've used yesterday as purchase date. "
                   "Is that correct?",
        "actions": ["confirm", "pick_date"]
    }
```

**Impulse detection query:**
```python
# Find non-consumable purchases in last 60 days
recent_purchases = db.purchases.find({
    "user_id": user_id,
    "order_date": { "$gte": sixty_days_ago },
    "is_consumable": False
})
# Send to Gemini for similarity check
```

---

## MongoDB Collection 3: nudges

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",

  "fired_at": "ISODate",
  "tier": "string (light|medium|hard)",
  "trigger_type": "string (budget_breach|duplicate_purchase|
                            frequency_pattern|pre_shop_check|
                            morning_alert)",

  "wallet_state_at_fire": "string (calm|aware|urgent|crisis)",
  "spend_pct_at_fire": "number",

  "context": {
    "platform": "string (nullable)",
    "similar_item": "string (nullable)",
    "similar_item_order_date": "ISODate (nullable)",
    "days_since_similar": "number (nullable)",
    "category_pct": "number (nullable)",
    "master_pct": "number (nullable)"
  },

  "gemini_copy": {
    "title": "string (generated nudge title)",
    "body": "string (generated nudge body)",
    "tag": "string (generated tag chip text)"
  },

  "user_response": "string (paused|overridden|pending)",
  "responded_at": "ISODate (nullable)",
  "transaction_followed": "boolean (nullable)",
  "amount_after_nudge": "number (nullable)"
}
```

**Indexes:**
```
{ user_id, fired_at }       → compound (report queries)
{ user_id, user_response }  → index (pause rate calculation)
```

---

## MongoDB Collection 4: monthly_reports

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",
  "month": "string (e.g. 2026-06)",
  "generated_at": "ISODate",

  "budget_summary": {
    "master_budget": "number (₹)",
    "total_spent": "number (₹, from BigQuery)",
    "utilisation_pct": "number",
    "category_breakdown": {
      "food_dining_delivery":   { "budget": 0, "spent": 0, "pct": 0 },
      "shopping_fashion":       { "budget": 0, "spent": 0, "pct": 0 },
      "electronics_tech":       { "budget": 0, "spent": 0, "pct": 0 },
      "entertainment_subs":     { "budget": 0, "spent": 0, "pct": 0 },
      "health_lifestyle":       { "budget": 0, "spent": 0, "pct": 0 },
      "others":                 { "budget": 0, "spent": 0, "pct": 0 }
    }
  },

  "nudge_summary": {
    "total_fired": "number",
    "total_paused": "number",
    "total_overridden": "number",
    "pause_rate_pct": "number",
    "estimated_saved": "number (₹)"
  },

  "streak_summary": {
    "best_streak_days": "number",
    "final_streak_days": "number"
  },

  "insights": {
    "top_impulse_category": "string",
    "top_impulse_platform": "string",
    "nudge_count_by_category": {},
    "gemini_insight_text": "string (AI summary)"
  },

  "wallet_state_distribution": {
    "days_calm": "number",
    "days_aware": "number",
    "days_urgent": "number",
    "days_crisis": "number"
  }
}
```

---

## API Endpoints

### Auth
```
POST /auth/register     → create user, return JWT
POST /auth/login        → validate credentials, return JWT
POST /auth/logout       → client clears token
```

### Wallet State
```
GET  /wallet-state      → { state: "aware", spend_pct: 58,
                             category_pcts: { ... } }
                           Reads spend totals from BigQuery
                           Saves state to MongoDB users collection
                           Called by frontend on every app open
                           Drives entire Living Wallet UI
```

### Budget
```
POST /budget/setup      → set master + category budgets
PUT  /budget/update     → update budget mid-month
GET  /budget/current    → current month budget + spend from BigQuery
```

### Transactions (BigQuery via Fivetran)
```
POST /transactions/sync     → call Fivetran MCP to trigger sync
                               Fivetran pushes to BigQuery
GET  /transactions/recent   → last 10 rows from BigQuery
GET  /transactions/summary  → month spend by category from BigQuery
```

### Purchases (MongoDB — item level)
```
POST /purchases/screenshot   → upload image
                                Gemini Vision extracts item details
                                order_date from receipt (not today)
                                Deduplication check runs
                                Returns: saved|already_logged
                                         |date_unconfirmed

POST /purchases/share        → receive shared content
                                Gemini extracts details
                                Same deduplication check
                                Returns: saved|already_logged
                                         |needs_screenshot

POST /purchases/manual       → 4-field form entry
                                Gemini tags item
                                Deduplication check runs

POST /purchases/confirm-date → user confirms estimated date

GET  /purchases/history      → last 60 days (non-consumable)
                                Used for impulse detection

POST /purchases/check        → pre-purchase check
                                Screenshot → Gemini Vision
                                Checks MongoDB purchase history
                                Returns: { is_clear, similar_item,
                                           days_since, nudge_needed }
```

### Nudges
```
POST /nudges/fire       → agent fires nudge, saves to MongoDB
POST /nudges/respond    → user response: paused|overridden
GET  /nudges/history    → all nudges this month
```

### Report
```
GET  /report/current-month  → reads BigQuery + MongoDB
                               generates full monthly report
GET  /report/history        → past months list
```

---

## Transaction Cleaner — Gemini Prompt

For real bank CSV data uploaded by users (future V2):

```
"Clean this raw bank transaction row.
 Bank format: {bank_format}
 Raw data: {raw_row}

 Return JSON only:
 {
   merchant: clean name (UPI-ZEPTO-9876-OKAXIS → Zepto),
   amount: number only,
   transaction_date: YYYY-MM-DD,
   is_debit: true if money left account,
   payment_method: upi|credit_card|debit_card|bnpl,
   category: food_dining_delivery|shopping_fashion|
             electronics_tech|entertainment_subs|
             health_lifestyle|others
 }
 If is_debit is false: return { skip: true }
 Return JSON only."
```

---

## Purchase Extractor — Gemini Prompt

For screenshot and share captures:

```
"Extract order details from this content.
 Content type: {screenshot|shared_text|shared_url}

 Return JSON only:
 {
   item_name: exact product name from receipt,
   platform: Myntra|Amazon|Flipkart|Zepto|
             Blinkit|Swiggy|Ajio|Nykaa|Other,
   amount: number only,
   order_date: date shown ON THE RECEIPT in YYYY-MM-DD.
               THIS IS NOT TODAY'S DATE.
               Read the actual date from the receipt.
               If no date visible: return null,
   category: food_dining_delivery|shopping_fashion|
             electronics_tech|entertainment_subs|
             health_lifestyle|others,
   is_consumable: true if grocery/medicine/daily essential,
                  false if clothing/electronics/lifestyle,
   subcategory: ethnic_wear|sneakers|skincare|gadget|
                subscription|etc
 }

 CRITICAL: order_date must come from receipt only.
           Never use today's date.
           If not visible: return null.
 Return JSON only."
```

---

## Auth Architecture

```
Method:   JWT (JSON Web Tokens)
Library:  python-jose
Expiry:   24 hours
Storage:  Frontend memory only (NEVER localStorage)
Password: bcrypt hash (never stored plaintext)
```

---

## Row-Level Security

Every MongoDB query MUST include user_id filter.
Every BigQuery query MUST include user context.
No user can ever read another user's data.

```python
# MongoDB — every query:
db.purchases.find({ "user_id": current_user_id, ... })
db.nudges.find({ "user_id": current_user_id, ... })

# BigQuery — filter by user context:
# For hackathon demo (single user):
# user context is implicit from JWT
```

---

## Sensitive Fields

| Field | Protection |
|---|---|
| password | bcrypt hash — never plaintext |
| JWT_SECRET_KEY | .env only |
| MONGODB_URI | .env only, never frontend |
| GEMINI_API_KEY | .env only, never frontend |
| GCP service account | .json file, gitignored |
| raw_extracted_text | MongoDB only, never sent to client |

---

## Data Retention

```
MongoDB purchases (impulse detection): 60 days active
MongoDB nudges: current + previous 2 months
MongoDB monthly_reports: kept indefinitely
BigQuery transactions: managed by Fivetran schedule
On account delete: all MongoDB records purged for user_id
```

---

*Document version: 3.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*
