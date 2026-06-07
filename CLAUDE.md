# SpendSense — Claude Code Instructions

## What I'm Building
SpendSense is an AI agent that stops impulse spending
before it happens. Built for Google Cloud Agent Builder
Hackathon 2026, Fivetran partner track.

## Read These Docs First
Before writing any code, read ALL of these:
- docs/SpendSense_PRD.md
  (what we're building, user stories, success metrics)
- docs/SpendSense_TRD.md
  (tech stack, folder structure, constraints)
- docs/SpendSense_AppFlow.md
  (every screen, every click, every state)
- docs/SpendSense_UIUXBrief.md
  (Living Wallet design system, 4 colour states)
- docs/SpendSense_BackendSchema.md
  (BigQuery + MongoDB schema, deduplication rules)
- docs/SpendSense_ImplementationPlan.md
  (build phases, done criteria, Claude Code prompts)

## Stack — Never Deviate
- Agent: Google Antigravity 2.0
- AI: Gemini 3.5 Flash (models/gemini-3.5-flash)
- Pipeline: Fivetran MCP → BigQuery (transactions)
- DB: MongoDB Atlas (users, purchases, nudges, reports)
- Backend: Python 3.11 + FastAPI
- Frontend: React 18 PWA + Tailwind CSS
- Hosting: Google Cloud Run
- 
## AI Model
Primary: Gemini API direct
Model: models/gemini-3.5-flash
Key: GEMINI_API_KEY from .env

Fallback: Vertex AI (if Gemini API has issues)
Model: gemini-3.5-flash on Vertex AI
Location: global (NOT us-central1)
Auth: GCP service account credentials
Project: GCP_PROJECT_ID from .env

Note: Gemini API is confirmed working.
Use Vertex AI only if Gemini API fails
or hits quota limits during demo.

## Critical Architecture Rules
- Transactions → BigQuery only (via Fivetran)
- Everything else → MongoDB only
- NEVER mix these two for any calculation
- Budget % always calculated from BigQuery
- Impulse detection always from MongoDB purchases
- No API keys in frontend — ever
- JWT in memory only — never localStorage

## Deduplication Rules
- Transactions: merchant + amount + date = unique
- Purchases: item_name + platform + amount
    + order_date = unique
- order_date = date FROM receipt, not upload date

## Wallet States
- calm:   0-40%  → ocean blue  #00B4D8
- aware:  40-70% → amber       #F77F00
- urgent: 70-85% → coral red   #E63946
- crisis: 85%+   → violet      #9B5DE5

## Nudge Tiers
- light:  informational only
- medium: contextual warning
- hard:   10-minute cooling off

## Current Progress
Phase 0: COMPLETE
- GitHub: github.com/Akshu2811/SpendSense
- Fivetran: Google Sheets → BigQuery syncing ✓
- MongoDB Atlas: GCP asia-south1 cluster ✓
- Gemini API: models/gemini-3.5-flash working ✓

## Rules for Claude Code
1. Read the relevant phase from ImplementationPlan before coding
2. Never suggest libraries not in TRD
3. Every function must handle errors gracefully
4. No silent failures — meaningful error messages always
5. Ask before making architectural decisions
6. Security headers and rate limiting are mandatory
7. Test each phase done criteria before moving to next