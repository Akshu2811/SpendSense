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
- `python-jose` — JWT token generation and validation
- `slowapi` — rate limiting middleware
- `python-multipart` — CSV file upload handling
- `pandas` — CSV parsing and transaction processing
- `httpx` — async HTTP calls to Gemini API

**Security middleware (all required on Day 4):**
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security
- Referrer-Policy: no-referrer

---

## Agent Orchestration

**Platform:** Google Antigravity 2.0
**Agent brain:** Gemini 3.5 Flash
**Agent pattern:** Multi-step reasoning loop

```
Step 1: Trigger received (manual or scheduled)
Step 2: Call Fivetran MCP → sync latest transactions
Step 3: Verify data freshness via Fivetran MCP
Step 4: Query MongoDB for transaction history (last 60 days)
Step 5: Gemini 3.5 Flash analyses patterns:
        - Budget breach risk
        - Duplicate purchase detection
        - Emotional/frequency pattern
Step 6: Determine nudge tier (light / medium / hard)
Step 7: Generate nudge message with specific context
Step 8: POST nudge to FastAPI → frontend renders popup
Step 9: Log user response to MongoDB
```

---

## Partner MCP Integration

**Primary Partner: Fivetran (submission track)**
- MCP server: Fivetran MCP via Google Antigravity tool registry
- Usage:
  - Trigger data sync on demand
  - Check sync status and data freshness
  - Configure new data source connectors
- Connectors used:
  - Google Sheets connector (for Google Pay CSV export)
  - File/CSV connector (for manual bank statement uploads)
- Sync schedule: Daily automatic + manual trigger on demand

**Supporting: MongoDB Atlas**
- MCP server: MongoDB Atlas MCP
- Usage: Store and query all app data
- Region: GCP asia-south1 (Mumbai) — data stays in India
- Tier: M0 free cluster for hackathon

---

## Database

**Provider:** MongoDB Atlas (M0 free tier)
**Type:** NoSQL document store
**Collections:** users, transactions, nudges, monthly_reports
*(Full schema in Document 05 — Backend Schema)*

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

**Frontend:** Firebase Hosting or Cloud Run static serve
- PWA build: `npm run build` → served as static files
- Custom domain: optional for hackathon

**Database:** MongoDB Atlas M0 (managed — no deployment needed)

**Agent:** Google Antigravity 2.0 (managed — no deployment needed)

---

## Third-Party APIs & Services

| Service | Purpose | Tier |
|---|---|---|
| Gemini 3.5 Flash API | Agent reasoning and nudge generation | Free tier (set $10 hard cap) |
| Fivetran MCP | Transaction data pipeline sync | Free trial |
| MongoDB Atlas | Transaction and nudge storage | M0 free forever |
| Google Cloud Run | Backend hosting | Free tier (2M requests/month) |
| Google AI Studio | Prototyping + one-click deploy | Free |
| Google Antigravity 2.0 | Agent orchestration | Free |
| Google Stitch | UI design generation | Free |

---

## Environment Variables

```
# Gemini
GEMINI_API_KEY=

# MongoDB
MONGODB_URI=
MONGODB_DB_NAME=spendsense

# Fivetran
FIVETRAN_API_KEY=
FIVETRAN_API_SECRET=
FIVETRAN_CONNECTOR_ID=

# Auth
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# GCP
GCP_PROJECT_ID=
CLOUD_RUN_REGION=us-central1

# App
APP_ENV=production
ALLOWED_ORIGINS=https://your-cloudrun-url.run.app
```

**Rules:**
- All variables in `.env` file — never hardcoded
- `.env` in `.gitignore` before first commit
- Frontend never receives any key — all calls go through backend

---

## Folder Structure

```
spendsense/
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
│   │   ├── transactions.py         # Transaction CRUD + upload
│   │   ├── nudges.py               # Nudge trigger + response
│   │   └── reports.py              # Monthly report generation
│   ├── services/
│   │   ├── gemini_service.py       # Gemini API calls
│   │   ├── fivetran_service.py     # Fivetran MCP calls
│   │   └── analysis_service.py    # Nudge tier decision logic
│   ├── models/
│   │   └── schemas.py              # Pydantic request/response models
│   ├── db/
│   │   └── mongodb.py              # MongoDB connection + queries
│   ├── middleware/
│   │   └── security.py             # Security headers + rate limiting
│   ├── .env                        # Never commit this
│   ├── .gitignore
│   ├── Dockerfile
│   └── requirements.txt
│
├── agent/
│   └── antigravity_config.yaml    # Antigravity agent definition
│
├── README.md
└── LICENSE                        # Open source license (required)
```

---

## Hard Technical Constraints

1. **No API keys in frontend** — ever. All Gemini, Fivetran, MongoDB
   calls go through FastAPI backend only.

2. **India-first** — all amounts in INR (₹). MongoDB region: asia-south1.
   No USD formatting anywhere in the UI.

3. **Free tier only** — entire stack must run at ₹0 cost during
   hackathon. Set hard caps on Gemini API before first deploy.

4. **PWA not native** — no React Native, no Android SDK.
   PWA on Chrome Android covers the demo requirement.

5. **Fivetran is primary MCP** — MongoDB MCP is supporting.
   All agent tool calls must prioritise Fivetran for data operations.

6. **Gemini 3.5 Flash only** — do not use Gemini Pro or other models.
   Flash is fast enough and stays within free quota.

7. **Google Antigravity 2.0 for orchestration** — no LangChain,
   no manual ADK setup. Antigravity handles the agent loop.

8. **Public GitHub repo required** — open source license file
   must be visible in the repo About section before submission.

---

*Document version: 1.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*
