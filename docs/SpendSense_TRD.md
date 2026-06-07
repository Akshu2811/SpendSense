# Document 02 — TRD: Technical Requirements Document
# SpendSense

---

## Frontend

**Framework:** React 18 (PWA — Progressive Web App)
**Styling:** Tailwind CSS
**Language:** JavaScript (JSX)
**Key libraries:**
- `react-router-dom` — page routing
- `recharts` — budget progress charts and spending graphs
- `react-hot-toast` — nudge notification toasts
- `axios` — API calls to FastAPI backend
- `date-fns` — transaction date formatting

**PWA requirements:**
- `manifest.json` — app name, icons, theme color
- Service worker — enables install to home screen on Android
- Push notification support via Web Push API (Android Chrome)

**Design source:** Google Stitch → export to React components

---

## Backend

**Framework:** Python 3.11 + FastAPI
**Key libraries:**
- `pymongo` — MongoDB connection
- `google-cloud-bigquery` — BigQuery connection for transactions
- `python-jose` — JWT token generation and validation
- `slowapi` — rate limiting middleware
- `python-multipart` — CSV file upload handling
- `pandas` — CSV parsing and transaction processing
- `httpx` — async HTTP calls to Gemini API
- `google-auth` — GCP authentication

**Security middleware (all required before deployment):**
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security
- Referrer-Policy: no-referrer

---

## Agent Orchestration

**Platform:** Google Antigravity 2.0
**Agent brain:** Gemini 3.5 Flash (models/gemini-3.5-flash)
**Agent pattern:** Multi-step reasoning loop

```
Step 1: Trigger received (manual or scheduled)
Step 2: Call Fivetran MCP → sync latest transactions to BigQuery
Step 3: Verify data freshness via Fivetran MCP
Step 4: Query BigQuery for spend totals and category breakdown
Step 5: Gemini 3.5 Flash analyses patterns:
        - Budget breach risk (from BigQuery totals)
        - Duplicate purchase detection (from MongoDB purchases)
        - Emotional/frequency pattern (from BigQuery frequency)
Step 6: Determine nudge tier (light / medium / hard)
Step 7: Generate nudge message with specific context
Step 8: POST nudge to FastAPI → frontend renders popup
Step 9: Log user response to MongoDB nudges collection
```

---

## Data Architecture — Critical

```
BIGQUERY — raw transaction data only
  Source: Fivetran syncs Google Sheets here
  Powers: budget % calculation, wallet state,
          category spend totals, spend frequency
  Read by: FastAPI backend via google-cloud-bigquery
  Dataset: spendsense_data
  Table: google_sheets.transactions

MONGODB — everything else
  Source: FastAPI writes directly
  Powers: user auth, purchase history,
          nudges, monthly reports
  Collections: users, purchases, nudges, monthly_reports
  NEVER stores raw transaction data
```

---

## Partner MCP Integration

**Primary Partner: Fivetran (submission track)**
- MCP server: Fivetran MCP via Google Antigravity tool registry
- Usage:
    - Trigger data sync on demand (Google Sheets → BigQuery)
    - Check sync status and data freshness
    - Verify last sync timestamp before agent analysis
- Connector: Google Sheets → BigQuery
- Sync schedule: Daily automatic + manual trigger on demand

**Supporting: MongoDB Atlas**
- MCP server: MongoDB Atlas MCP
- Usage: Store and query user data, purchases, nudges, reports
- Region: GCP asia-south1 (Mumbai) — data stays in India
- Tier: M0 free cluster for hackathon

---

## Database Split

**BigQuery (GCP) — transaction data**
- Provider: Google BigQuery
- Project: spendsense-[id]
- Dataset: spendsense_data
- Table: google_sheets.transactions
- Filled by: Fivetran pipeline automatically
- Read by: FastAPI for budget calculations only

**MongoDB Atlas — application data**
- Provider: MongoDB Atlas M0 free tier
- Collections: users, purchases, nudges, monthly_reports
- Filled by: FastAPI on user actions
- Full schema in Document 05 — Backend Schema

---

## Authentication

**Method:** JWT (JSON Web Tokens)
**Library:** `python-jose`
**Flow:**
- User registers with username + password
- Backend returns signed JWT token (24-hour expiry)
- Frontend stores token in memory (not localStorage)
- All protected API routes validate token on every request
  **Scope:** Single user demo account for hackathon
  (no email verification, no OAuth for MVP)

---

## Hosting & Deployment

**Backend + Agent:** Google Cloud Run (us-central1)
- Deployed via Google AI Studio one-click deploy
- Dockerfile: multi-stage Python build
- Port: 8080 (Cloud Run default)
- Auto-scaling: min 0, max 2 instances (free tier)
- Change to min 1 instance on demo day (avoid cold start)

**Frontend:** Firebase Hosting or Cloud Run static serve
- PWA build: `npm run build` → served as static files
- Custom domain: optional for hackathon

**BigQuery:** Managed by GCP — no deployment needed
**MongoDB Atlas:** Managed — no deployment needed
**Agent:** Google Antigravity 2.0 — managed — no deployment needed

---

## Third-Party APIs & Services

| Service | Purpose | Tier |
|---|---|---|
| Gemini 3.5 Flash API | Agent reasoning and nudge generation | Free (set $10 hard cap) |
| Fivetran MCP | Transaction data pipeline sync | Free 14-day trial |
| Google BigQuery | Raw transaction storage + spend queries | Free 10GB/month |
| MongoDB Atlas | User data, purchases, nudges, reports | M0 free forever |
| Google Cloud Run | Backend hosting | Free 2M requests/month |
| Google AI Studio | Prototyping + one-click deploy | Free |
| Google Antigravity 2.0 | Agent orchestration | Free |
| Google Stitch | UI design generation | Free |

---

## Environment Variables

```
# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=models/gemini-3.5-flash

# MongoDB
MONGODB_URI=
MONGODB_DB_NAME=spendsense

# BigQuery
GCP_PROJECT_ID=
BIGQUERY_DATASET=spendsense_data
BIGQUERY_TABLE=google_sheets.transactions
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Fivetran
FIVETRAN_API_KEY=
FIVETRAN_API_SECRET=
FIVETRAN_CONNECTOR_ID=

# Auth
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# GCP
CLOUD_RUN_REGION=us-central1

# App
APP_ENV=production
ALLOWED_ORIGINS=https://your-cloudrun-url.run.app
```

**Rules:**
- All variables in `.env` file — never hardcoded
- `.env` in `.gitignore` before first commit
- Frontend never receives any key — all calls go through backend
- service-account.json in `.gitignore` — never commit

---

## Folder Structure

```
spendsense/
├── docs/                          # All 6 MD documents
├── frontend/
│   ├── public/
│   │   ├── manifest.json          # PWA config
│   │   └── service-worker.js      # PWA offline support
│   ├── src/
│   │   ├── components/
│   │   │   ├── NudgePopup.jsx      # Core nudge overlay card
│   │   │   ├── BudgetBar.jsx       # Progress bar component
│   │   │   ├── TransactionFeed.jsx # Recent transactions list
│   │   │   ├── StreakCounter.jsx   # Gamified streak display
│   │   │   └── MonthlyReport.jsx   # End of month report card
│   │   ├── pages/
│   │   │   ├── Onboarding.jsx      # Budget setup + data connect
│   │   │   ├── Dashboard.jsx       # Main screen
│   │   │   ├── ShopCheck.jsx       # Pre-purchase check screen
│   │   │   ├── AddPurchase.jsx     # Screenshot/share/manual
│   │   │   └── Report.jsx          # Monthly report screen
│   │   ├── services/
│   │   │   └── api.js              # All axios API calls
│   │   └── App.jsx
│   └── package.json
│
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── routers/
│   │   ├── auth.py                 # Login/register endpoints
│   │   ├── transactions.py         # BigQuery queries + sync
│   │   ├── purchases.py            # Screenshot/share/manual
│   │   ├── nudges.py               # Nudge trigger + response
│   │   └── reports.py              # Monthly report generation
│   ├── services/
│   │   ├── gemini_service.py       # Gemini API calls
│   │   ├── fivetran_service.py     # Fivetran MCP calls
│   │   ├── bigquery_service.py     # BigQuery read queries
│   │   ├── analysis_service.py     # Wallet state + nudge logic
│   │   └── transaction_cleaner.py  # Gemini cleans raw bank CSV
│   ├── models/
│   │   └── schemas.py              # Pydantic request/response models
│   ├── db/
│   │   ├── mongodb.py              # MongoDB connection + queries
│   │   └── bigquery.py             # BigQuery connection + queries
│   ├── middleware/
│   │   └── security.py             # Security headers + rate limiting
│   ├── .env                        # Never commit this
│   ├── Dockerfile
│   └── requirements.txt
│
├── agent/
│   └── antigravity_config.yaml    # Antigravity agent definition
│
├── .gitignore
├── README.md
└── LICENSE                        # MIT — required for submission
```

---

## Hard Technical Constraints

1. **No API keys in frontend** — ever. All Gemini, Fivetran,
   BigQuery, MongoDB calls go through FastAPI backend only.

2. **India-first** — all amounts in INR (₹).
   MongoDB region: asia-south1. BigQuery: GCP.
   No USD formatting anywhere in the UI.

3. **Free tier only** — entire stack must run at ₹0 cost.
   Set hard caps on Gemini API before first deploy.
   BigQuery free tier: 10GB storage + 1TB queries/month.

4. **PWA not native** — no React Native, no Android SDK.
   PWA on Chrome Android covers the demo requirement.

5. **Fivetran is primary MCP** — all transaction data
   flows through Fivetran → BigQuery pipeline.
   Agent must call Fivetran MCP before every analysis.

6. **BigQuery for transactions, MongoDB for everything else**
   — never reverse this. Budget % always from BigQuery.
   Impulse detection always from MongoDB purchases.

7. **Gemini 3.5 Flash only** — model: models/gemini-3.5-flash
   Do not use other models. Stays within free quota.

8. **Google Antigravity 2.0 for orchestration** — no LangChain,
   no manual ADK setup. Antigravity handles the agent loop.

9. **Public GitHub repo required** — MIT LICENSE file
   must be visible in the repo About section before submission.

---

*Document version: 2.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*

