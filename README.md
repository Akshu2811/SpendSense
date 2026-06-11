# SpendSense 💸
### AI agent that stops impulse spending before it happens.

> Built for the Google Cloud Agent Builder Hackathon 2026  
> Partner track: Fivetran  
> Stack: Gemini 3.1 Flash Lite · Google ADK · Fivetran MCP · FastAPI · React PWA

---

## The Problem

GenZ salaried professionals in Indian metros consistently
reach end-of-month with depleted savings — not from big
purchases, but from 47 small ones they didn't think about.

No existing tool intercepts them at the moment of temptation
with enough context to make them pause.

**SpendSense fixes that.**

---

## What SpendSense Does

SpendSense is the first AI agent that intercepts impulse
purchases **before** they happen — not after.

| Layer | Trigger | What happens |
|---|---|---|
| Morning Alert | 9 AM daily | Wallet state + spending position delivered |
| Pre-Shop Check | Before opening any app | Nudge fires with budget + purchase history |
| Item Check | Screenshot of product | Duplicate detection against 60-day history |

---

## How It Works

```
User opens SpendSense → React PWA calls FastAPI backend →
Google ADK agent runs:
  1. Calls Fivetran MCP → triggers Google Sheets sync → BigQuery
  2. Reads wallet state from BigQuery (spend totals)
  3. Reads purchase history from MongoDB (item details)
  4. Gemini 3.1 Flash Lite analyses patterns
  5. Fires calibrated nudge with GenZ copy back to user
```

Two data stores, two purposes — never mixed:
- **MongoDB** → item-level purchase memory, nudges, users, reports
- **BigQuery** → raw transaction data from bank CSV via Fivetran

---

## Fivetran MCP Integration

Fivetran is the partner MCP powering SpendSense's transaction data pipeline:

- Connector: Google Sheets → BigQuery
- Trigger: on-demand via ADK agent tool call
- Agent verifies data freshness before every analysis
- Wallet state always based on fresh transaction data

The Google ADK agent calls Fivetran MCP as its **first step**
before any spending analysis — ensuring nudge decisions are
always based on the latest transaction data.

---

## The Living Wallet

SpendSense's entire UI shifts dynamically based on wallet health:

| State | Trigger | Colour | Mood Text |
|---|---|---|---|
| Calm | 0–40% spent | Ocean Blue `#00B4D8` | "breathing easy ✦" |
| Aware | 40–70% spent | Warm Amber `#F77F00` | "heads up, bestie 👀" |
| Urgent | 70–85% spent | Coral Red `#E63946` | "feeling the heat 🌶️" |
| Crisis | 85%+ spent | Electric Violet `#9B5DE5` | "wallet in crisis 💀" |

Background, orb, mood text, nudge tone — everything shifts
simultaneously with a 1.5s CSS transition.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | Google ADK (google-adk 2.2.0) |
| AI Model | Gemini 3.1 Flash Lite via Vertex AI |
| Data Pipeline | Fivetran MCP → BigQuery |
| Backend | FastAPI (Python 3.11) |
| Frontend | React 18 PWA + Tailwind CSS |
| Primary DB | MongoDB Atlas (M0, ap-south-1) |
| Analytics DB | Google BigQuery (GCP) |
| Hosting | Google Cloud Run |

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account
- Google Cloud project with Vertex AI enabled
- Fivetran account
- gcloud CLI installed and authenticated

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

gcloud auth application-default login
gcloud config set project spendsense-498709

python -m uvicorn main:app --reload --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm start
# Opens at http://localhost:3000
```

### Environment Variables
Create `backend/.env`:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/spendsense
MONGODB_DB_NAME=spendsense
GCP_PROJECT_ID=spendsense-498709
GCP_LOCATION=us-central1
GOOGLE_GENAI_API_KEY=your_key_here
FIVETRAN_API_KEY=your_key_here
FIVETRAN_API_SECRET=your_secret_here
FIVETRAN_CONNECTOR_ID=your_connector_id
JWT_SECRET_KEY=your_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Demo Account
```
Username: akki_test
Password: test1234
```
Pre-loaded with 15 purchases, 27 nudges, 58% budget spent
(aware/amber state) for demo purposes.

---

## Project Structure
```
SpendSense/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── transactions.py
│   │   ├── purchases.py
│   │   ├── nudges.py
│   │   ├── reports.py
│   │   └── agent.py
│   ├── services/
│   │   ├── gemini_service.py
│   │   ├── bigquery_service.py
│   │   ├── analysis_service.py
│   │   └── fivetran_service.py
│   └── db/
│       ├── mongodb.py
│       └── bigquery.py
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       └── services/
├── agent/
│   └── spendsense_agent/
└── docs/
    ├── SpendSense_PRD.md
    ├── SpendSense_TRD.md
    ├── SpendSense_BackendSchema.md
    ├── SpendSense_UIUXBrief.md
    ├── SpendSense_AppFlow.md
    └── SpendSense_ImplementationPlan.md
```

---

## Judging Criteria

| Criterion | How SpendSense addresses it |
|---|---|
| Technological Implementation | Google ADK + Gemini 3.1 Flash Lite + Fivetran MCP — multi-step agent with real tool calls |
| Design | Living Wallet — 4 reactive states, mobile-first PWA, GenZ-native tone |
| Potential Impact | 400M+ GenZ users in India face this exact problem |
| Quality of Idea | First AI agent to intercept impulse spending before it happens |

---

## Hackathon
- **Competition:** Google Cloud Agent Builder 2026
- **Partner Track:** Fivetran
- **License:** MIT

---

## License
MIT — see [LICENSE](LICENSE) file