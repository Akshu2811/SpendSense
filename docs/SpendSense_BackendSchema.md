# Document 05 — Backend Schema
# SpendSense

---

## Database Provider
MongoDB Atlas — M0 free tier
Region: GCP asia-south1 (Mumbai) — data stays in India
Database name: spendsense

---

## Collections Overview

| Collection | Purpose |
|---|---|
| users | Auth + budget settings + wallet state |
| transactions | All UPI/card spending data from Fivetran |
| purchases | Item-level data from screenshot/share/manual |
| nudges | Every nudge fired + user response |
| monthly_reports | Auto-generated end-of-month summaries |

---

## Collection 1: users

Stores auth credentials, budget configuration, and current wallet state.

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
    "month_set": "string (e.g. '2026-06')"
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
    "sync_method": "string (csv|googlepay|manual)"
  },

  "preferences": {
    "notification_time": "string (default: '09:00')",
    "timezone": "string (default: 'Asia/Kolkata')"
  }
}
```

**Indexes:**
- `username` → unique index (fast login lookup)
- `wallet_state.current` → index (dashboard load)

---

## Collection 2: transactions

Stores all payment-level transaction data from Fivetran pipeline.
This powers: budget tracking, spend %, wallet state calculation.
Does NOT store item details — that's in purchases collection.

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",

  "amount": "number (₹, positive, required)",
  "merchant": "string (e.g. 'Myntra', 'Zepto')",
  "category": "string (food_dining_delivery|shopping_fashion|
                        electronics_tech|entertainment_subs|
                        health_lifestyle|others)",
  "payment_method": "string (upi|credit_card|debit_card|
                              bnpl|net_banking|wallet)",
  "transaction_date": "ISODate (required)",

  "source": "string (fivetran_csv|fivetran_googlepay|manual)",
  "raw_description": "string (original SMS/CSV text)",
  "fivetran_sync_id": "string (nullable, for deduplication)",

  "created_at": "ISODate (when imported to MongoDB)"
}
```

**Indexes:**
- `user_id` + `transaction_date` → compound index (dashboard queries)
- `user_id` + `category` → compound index (category budget calc)
- `fivetran_sync_id` → unique index (prevent duplicate imports)

**Key queries this enables:**
```
Total spent this month:
  db.transactions.aggregate([
    { $match: { user_id, transaction_date: { $gte: month_start } } },
    { $group: { _id: null, total: { $sum: "$amount" } } }
  ])

Spend by category:
  db.transactions.aggregate([
    { $match: { user_id, transaction_date: { $gte: month_start } } },
    { $group: { _id: "$category", total: { $sum: "$amount" } } }
  ])
```

---

## Collection 3: purchases

Stores item-level purchase data from screenshot/share/manual entry.
This powers: duplicate detection, smart nudges, purchase history.
Separate from transactions — transactions = money moved,
purchases = what was actually bought.

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",

  "item_name": "string (e.g. 'Blue Printed Kurta')",
  "item_description": "string (full extracted description)",
  "category": "string (same enum as transactions)",
  "subcategory": "string (e.g. 'ethnic_wear', 'sneakers')",

  "amount": "number (₹)",
  "platform": "string (Myntra|Amazon|Flipkart|Zepto|
                        Blinkit|Swiggy|Ajio|Other)",
  "purchase_date": "ISODate",

  "capture_method": "string (screenshot|share|manual)",
  "raw_image_text": "string (Gemini Vision extracted text)",

  "gemini_tags": ["array of semantic tags for similarity matching"],
  "embedding_summary": "string (for Gemini similarity comparison)",

  "is_consumable": "boolean (true=grocery/medicine, false=clothing/electronics)",

  "created_at": "ISODate"
}
```

**Indexes:**
- `user_id` + `purchase_date` → compound index
- `user_id` + `platform` → compound index (platform-specific checks)
- `user_id` + `is_consumable` → index (skip consumables in duplicate check)

**How duplicate detection works:**
```
New purchase attempt detected
        ↓
Query: find purchases where
  user_id = current user
  purchase_date >= 60 days ago
  is_consumable = false
        ↓
Send results + new item to Gemini:
"Compare this new item with the
 user's recent purchases. Is there
 a semantically similar item in
 the last 60 days?"
        ↓
Gemini returns: similar/not similar
+ which item matched + days since purchase
```

---

## Collection 4: nudges

Every nudge fired is logged with full context and user response.
This powers: monthly report, pause rate calculation, streak tracking.

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",

  "fired_at": "ISODate (when nudge triggered)",

  "tier": "string (light|medium|hard)",
  "trigger_type": "string (budget_breach|duplicate_purchase|
                            frequency_pattern|pre_shop_check|
                            morning_alert)",

  "wallet_state_at_fire": "string (calm|aware|urgent|crisis)",
  "spend_pct_at_fire": "number",

  "context": {
    "platform": "string (nullable)",
    "similar_item": "string (nullable)",
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
  "amount_after_nudge": "number (nullable, ₹ spent after override)"
}
```

**Indexes:**
- `user_id` + `fired_at` → compound index (report queries)
- `user_id` + `user_response` → index (pause rate calculation)

---

## Collection 5: monthly_reports

Auto-generated summary at end of each month.
Also generated on demand from /report screen.

```json
{
  "_id": "ObjectId (auto)",
  "user_id": "ObjectId (ref: users._id, required)",
  "month": "string (e.g. '2026-06')",
  "generated_at": "ISODate",

  "budget_summary": {
    "master_budget": "number (₹)",
    "total_spent": "number (₹)",
    "utilisation_pct": "number",
    "category_breakdown": {
      "food_dining_delivery": { "budget": 0, "spent": 0, "pct": 0 },
      "shopping_fashion": { "budget": 0, "spent": 0, "pct": 0 },
      "electronics_tech": { "budget": 0, "spent": 0, "pct": 0 },
      "entertainment_subs": { "budget": 0, "spent": 0, "pct": 0 },
      "health_lifestyle": { "budget": 0, "spent": 0, "pct": 0 },
      "others": { "budget": 0, "spent": 0, "pct": 0 }
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
    "nudge_count_by_category": { },
    "gemini_insight_text": "string (AI-generated summary)"
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
POST /auth/register    → create user, return JWT
POST /auth/login       → validate, return JWT
POST /auth/logout      → client clears token
```

### Wallet State
```
GET  /wallet-state     → returns current state string + pct
                         { state: "aware", pct: 58 }
                         Frontend reads this on every app open
```

### Budget
```
POST /budget/setup     → set master + category budgets
PUT  /budget/update    → update budget mid-month
GET  /budget/current   → get current month budget + spend
```

### Transactions
```
POST /transactions/upload-csv   → Fivetran CSV import trigger
GET  /transactions/recent       → last 10 transactions
GET  /transactions/summary      → month spend by category
```

### Purchases (Item Level)
```
POST /purchases/screenshot      → upload image → Gemini Vision
POST /purchases/share           → receive shared content
POST /purchases/manual          → manual 4-field entry
GET  /purchases/history         → last 60 days purchases
POST /purchases/check           → pre-purchase check (screenshot)
                                   returns: similar/clear + nudge
```

### Nudges
```
POST /nudges/fire               → agent fires nudge, logs it
POST /nudges/respond            → user response (paused/overridden)
GET  /nudges/history            → all nudges this month
```

### Report
```
GET  /report/current-month      → generate/fetch monthly report
GET  /report/history            → past months list
```

---

## Auth Architecture

Method: JWT (JSON Web Tokens)
Library: python-jose
Token expiry: 24 hours
Storage: Frontend memory only (never localStorage)
All protected routes: validate JWT on every request

Password: bcrypt hashing (never stored plaintext)
No email verification for hackathon MVP
No OAuth for hackathon MVP

---

## Row-Level Security Rules

Every query MUST include user_id filter.
No user can ever read another user's data.
Enforced at service layer in FastAPI — not just DB level.

```python
# Every query pattern:
db.transactions.find({ "user_id": current_user_id, ... })
db.purchases.find({ "user_id": current_user_id, ... })
db.nudges.find({ "user_id": current_user_id, ... })
```

---

## Sensitive Fields

| Field | Protection |
|---|---|
| password | bcrypt hash — never stored plaintext |
| JWT_SECRET_KEY | .env only — never in code |
| MONGODB_URI | .env only — never in code |
| fivetran_connector_id | .env + server-side only |
| raw_image_text | stored in MongoDB, never returned to client in full |

---

## Data Retention

Active purchase history: 60 days (used for duplicate detection)
Transactions: current month + previous 2 months
Nudges: current month + previous 2 months
Monthly reports: kept indefinitely (small documents)
On account delete: all collections purged for that user_id

---

*Document version: 1.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*
