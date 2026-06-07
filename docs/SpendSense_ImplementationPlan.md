# Document 06 — Implementation Plan
# SpendSense

---

## Overview

Total build time: 5 days (June 5–9, 2026)
Buffer day: June 10 (demo polish + submission)
Deadline: June 11, 2026

Daily schedule: 9:30 AM – 5:00 PM (shift starts 5 PM)
Effective build hours per day: ~6 hours
Total build hours: ~30 hours

Rule: Never start a phase without completing the previous one.
Rule: Claude Code is open for every phase from Day 1.
Rule: No new features after Day 4, 3 PM. Polish only.

---

## Phase Overview

| Phase | Day | Goal | Done When |
|---|---|---|---|
| 1 | Day 1 AM | Project setup + repo | Code runs locally |
| 2 | Day 1 PM | MongoDB + auth | Login works end-to-end |
| 3 | Day 2 AM | Fivetran pipeline | Transactions in MongoDB |
| 4 | Day 2 PM | Wallet state agent | State calculated correctly |
| 5 | Day 3 AM | Gemini reasoning | Nudge generated correctly |
| 6 | Day 3 PM | UI — Living Wallet | Dashboard renders all 4 states |
| 7 | Day 4 AM | Purchase capture | Screenshot + Gemini Vision works |
| 8 | Day 4 PM | Nudge system | Full nudge flow end-to-end |
| 9 | Day 5 AM | PWA + deploy | Hosted URL accessible |
| 10 | Day 5 PM | Security + report | All checklist items done |
| 11 | Day 6 | Demo + submission | Video recorded, Devpost submitted |

---

## Day 1 — Foundation

### Phase 0: Pre-Setup — Do This Before Everything (9:30 AM – 10:30 AM)

Goal: All external accounts created and verified.
      Fivetran pipeline working with sample data.
      Nothing else starts until this is done.

Steps:
1. Fivetran setup (YOU ARE HERE ✓):
   - Select source: Google Sheets
   - Create Google Sheet: SpendSense_Transactions
     Columns: date, merchant, amount, category, payment_method
     Add 15-20 sample rows (use data from implementation plan)
   - Connect Google account to Fivetran
   - Select destination: MongoDB Atlas
   - Enter MongoDB Atlas connection URI
   - Run first sync → verify rows appear in MongoDB
   - Done when: data visible in MongoDB Atlas collections

2. MongoDB Atlas:
   - Create M0 free cluster
   - Region: aws-ap-south-1 (Mumbai)
   - Get connection URI → save to .env
   - Create database: spendsense

3. Google Cloud:
   - Create project: spendsense-[yourname]
   - Enable APIs: Cloud Run, Gemini API
   - Get Gemini API key → save to .env

4. Google Antigravity 2.0:
   - Create new agent project
   - Name: SpendSense Agent
   - Leave empty for now — wire on Day 2

5. GitHub:
   - Create public repo: SpendSense
   - Add MIT LICENSE file immediately
   - Add .gitignore (include .env)
   - Clone to local machine

Done criteria:
☐ Fivetran sync runs successfully
☐ Sample transactions visible in MongoDB Atlas
☐ Gemini API key tested and working
☐ GitHub repo public with LICENSE visible
☐ All credentials saved in .env file

---

### Phase 1: Project Setup (10:30 AM – 12:30 PM)

Goal: Clean repo, folder structure, environment variables,
      all tools connected, blank app runs locally.

Steps:
1. Create GitHub repo (public, MIT license added immediately)
   - Repo name: SpendSense
   - Add LICENSE file — required for hackathon submission
   - Add .gitignore — include .env before first commit

2. Set up folder structure exactly as defined in TRD:
   spendsense/
   ├── frontend/
   ├── backend/
   ├── agent/
   └── README.md

3. Backend setup (Claude Code):
   - Create virtual environment: python -m venv venv
   - Install: fastapi uvicorn pymongo python-jose
             slowapi python-multipart pandas httpx
             python-dotenv bcrypt
   - Create main.py with FastAPI app skeleton
   - Test: uvicorn main:app --reload → 200 OK

4. Frontend setup (Claude Code):
   - npx create-react-app frontend --template cra-template-pwa
   - Install: axios react-router-dom recharts date-fns
             react-hot-toast
   - Tailwind CSS setup
   - Test: npm start → blank app loads

5. Environment variables:
   - Create backend/.env with all keys from TRD
   - Verify .env is in .gitignore
   - Run grep check for exposed keys

6. Google tools setup:
   - Google AI Studio: create project, get Gemini API key
   - MongoDB Atlas: create M0 cluster, get connection URI
   - Google Cloud: create project spendsense-[id]
   - Antigravity 2.0: create new agent project

Done criteria:
☐ GitHub repo is public with LICENSE visible
☐ .env is gitignored and verified
☐ FastAPI returns 200 on GET /health
☐ React app loads in browser
☐ All API keys are in .env and tested

---

### Phase 2: Database + Auth (1:30 PM – 5:00 PM)

Goal: User can register and login. JWT works.
      MongoDB collections created with correct indexes.

Steps:
1. MongoDB connection (Claude Code):
   - Create backend/db/mongodb.py
   - Connect using MONGODB_URI from .env
   - Test connection on startup

2. Create all 5 collections with indexes:
   - users (username unique index)
   - transactions (user_id + date compound)
   - purchases (user_id + date compound)
   - nudges (user_id + fired_at compound)
   - monthly_reports (user_id + month compound)
   - Seed one test user for development

3. Auth endpoints (Claude Code):
   - POST /auth/register → hash password, create user, return JWT
   - POST /auth/login → validate, return JWT
   - JWT middleware → protect all non-auth routes
   - Test with Postman or curl

4. Pydantic schemas:
   - Create backend/models/schemas.py
   - UserCreate, UserLogin, TokenResponse schemas

Done criteria:
☐ POST /auth/register returns JWT token
☐ POST /auth/login returns JWT token
☐ Invalid credentials return 401
☐ Protected route rejects request without token
☐ All 5 MongoDB collections exist with indexes

---

## Day 2 — Agent Core

### Phase 3: Fivetran Pipeline (9:30 AM – 12:30 PM)

Goal: Fivetran connected. Transactions flowing into MongoDB.

Steps:
1. Fivetran account setup:
   - Sign up at fivetran.com (free trial)
   - Create connector: Google Sheets or CSV file type
   - Prepare sample UPI transaction CSV:
     date, merchant, amount, category, payment_method
     2026-06-01, Zepto, 340, food_dining_delivery, upi
     2026-06-02, Myntra, 899, shopping_fashion, credit_card
     (create 20-30 realistic sample transactions)

2. Fivetran MCP integration (Antigravity):
   - Add Fivetran MCP to Antigravity agent tools
   - Test: agent calls Fivetran MCP → sync triggers → data arrives

3. Transaction ingestion endpoint (Claude Code):
   - POST /transactions/sync-fivetran
     → calls Fivetran MCP to trigger sync
     → reads synced data
     → deduplicates using fivetran_sync_id
     → saves to transactions collection
   - GET /transactions/recent → returns last 10

4. Category mapping service:
   - Map merchant names to categories automatically
   - Zepto/Blinkit/Swiggy → food_dining_delivery
   - Myntra/Amazon/Flipkart → shopping_fashion
   - etc.

Done criteria:
☐ Fivetran connector configured and tested
☐ POST /transactions/sync-fivetran triggers sync
☐ Transactions appear in MongoDB after sync
☐ Duplicate transactions are not imported twice
☐ Categories are correctly assigned

---

### Phase 4: Wallet State Agent (1:30 PM – 5:00 PM)

Goal: Antigravity agent calculates wallet state correctly.
      /wallet-state endpoint returns correct state.

Steps:
1. Spend calculation service (Claude Code):
   - Create backend/services/analysis_service.py
   - calculate_spend_pct(user_id, month) function
   - calculate_category_pcts(user_id, month) function
   - determine_wallet_state(spend_pct) function:
     < 40% → calm
     40–70% → aware
     70–85% → urgent
     85%+ → crisis

2. Antigravity agent — wallet state logic:
   - Create agent/antigravity_config.yaml
   - Define agent trigger: on Fivetran sync complete
   - Agent step 1: call calculate_spend_pct
   - Agent step 2: call determine_wallet_state
   - Agent step 3: update users.wallet_state in MongoDB
   - Agent step 4: call /wallet-state to verify

3. Wallet state endpoint (Claude Code):
   - GET /wallet-state
     → reads users.wallet_state from MongoDB
     → returns { state, spend_pct, category_pcts }
   - This is the endpoint the frontend calls on every load

4. Test all 4 states manually:
   - Insert transactions to reach 32% → verify calm
   - Insert more to reach 58% → verify aware
   - Insert more to reach 79% → verify urgent
   - Insert more to reach 91% → verify crisis

Done criteria:
☐ Agent triggers after Fivetran sync
☐ All 4 states calculated correctly
☐ GET /wallet-state returns correct state string
☐ MongoDB users.wallet_state updated after each sync
☐ Category percentages calculated correctly

---

## Day 3 — Intelligence + UI

### Phase 5: Gemini Reasoning Layer (9:30 AM – 12:30 PM)

Goal: Gemini generates nudge copy. Duplicate detection works.
      Notification copy is state-aware and GenZ-toned.

Steps:
1. Gemini service (Claude Code):
   - Create backend/services/gemini_service.py
   - Function: generate_nudge_copy(state, pct, platform,
                                    similar_item, category_pct)
   - Prompt template:
     "User wallet state: {state}
      Overall budget: {pct}% used
      Platform: {platform}
      Similar item bought: {similar_item} ({days} days ago)
      Category budget: {category_pct}% used

      Generate a SpendSense push notification for a GenZ
      Indian user. Two parts:
      1. title: punchy, max 8 words, GenZ language
      2. body: specific, mention real numbers, max 15 words

      Tone rules:
      - calm state: friendly, light, encouraging
      - aware state: funny, slightly dramatic
      - urgent state: sarcastic, concerned, relatable
      - crisis state: unhinged, dramatic, but never shameful
      - Always reference Indian context (zepto, myntra, maggi)
      - Never use formal language
      - Never shame the user

      Return JSON only: { title, body, tag }"

2. Duplicate detection service (Claude Code):
   - Function: check_duplicate(user_id, new_item_description)
   - Query purchases (last 60 days, is_consumable=false)
   - Send to Gemini: "Is {new_item} semantically similar
     to any of these recent purchases: {purchase_list}?"
   - Gemini returns: { is_duplicate, matched_item, days_ago }

3. Morning notification generator:
   - Scheduled function (runs at notification_time from users)
   - Reads current wallet state
   - Generates state-appropriate morning copy via Gemini
   - Queues PWA push notification

4. Test Gemini outputs:
   - Test all 4 states → verify tone matches
   - Test duplicate detection with similar items
   - Test duplicate detection with dissimilar items
   - Test consumable skip (grocery vs grocery = not duplicate)

Done criteria:
☐ Gemini generates valid JSON nudge copy
☐ Tone matches wallet state correctly
☐ Duplicate detection returns correct result
☐ Consumables never flagged as duplicates
☐ Morning notification generates correctly

---

### Phase 6: Living Wallet UI (1:30 PM – 5:00 PM)

Goal: Dashboard renders. All 4 wallet states display correctly.
      UI is built with Google Stitch, wired to FastAPI.

Steps:
1. Google Stitch — generate components:
   Prompt 1: "Dark mobile PWA dashboard. Large breathing
   glowing orb in center. Orb colour and background shift
   based on state variable (calm=ocean blue, aware=amber,
   urgent=coral red, crisis=electric violet). Background is
   deep dark (#050D1A base). Glass morphism cards. Bottom
   tab navigation. React + Tailwind."

   Prompt 2: "Bottom sheet nudge popup. Glass card slides
   up from bottom. Drag pill at top. Emoji + title + body
   + mini progress bar + two buttons (skip/wait). Dark theme.
   State-aware accent colour."

   Prompt 3: "Monthly report screen. Dark background. Three
   stat cards in a row. Large savings amount card. Horizontal
   budget bar. Insight card at bottom."

2. Export from Stitch → copy to frontend/src/components/

3. Wire state to UI (Claude Code):
   - Frontend calls GET /wallet-state on load
   - Applies CSS class: .state-calm / .state-aware etc.
   - CSS transition: 1.5s ease on all colour properties
   - Orb pulse animation: CSS keyframes

4. Build remaining screens:
   - Onboarding: budget setup form → category breakdowns
   - Login / Register screens
   - Settings screen
   - Add Purchase screen (3 options)
   - Shop Check screen (app grid)

5. PWA setup:
   - manifest.json: name, icons, theme_color, display:standalone
   - Service worker: offline support
   - Test install to Android home screen

Done criteria:
☐ Dashboard loads and shows correct wallet state
☐ All 4 colour states render correctly
☐ State transitions animate smoothly (1.5s)
☐ Orb pulses on idle
☐ App installs to Android home screen as PWA
☐ Bottom navigation works between screens

---

## Day 4 — Features + Integration

### Phase 7: Purchase Capture (9:30 AM – 12:00 PM)

Goal: All 3 capture methods work. Item details stored correctly.

Steps:
1. Screenshot upload (Claude Code):
   - POST /purchases/screenshot
   - Accept image file (multipart/form-data)
   - Send to Gemini Vision:
     "Extract order details from this screenshot.
      Return JSON: { item_name, platform, amount,
      category, purchase_date, is_consumable }"
   - Validate response
   - Save to purchases collection
   - Show preview to user before confirming

2. Share button handler (Claude Code):
   - POST /purchases/share
   - Accept text or URL
   - If URL: attempt fetch → extract text
   - If blocked: return { needs_screenshot: true }
   - Send text to Gemini for extraction
   - Save to purchases collection

3. Manual entry (Claude Code):
   - POST /purchases/manual
   - Accept 4 fields: item_name, platform, amount, category
   - Gemini tags the item for future similarity matching
   - Save to purchases collection

4. Pre-purchase check (Claude Code):
   - POST /purchases/check
   - Accept image of product being considered
   - Gemini Vision extracts: item description
   - Run duplicate detection against history
   - Return: { is_clear, similar_item, days_ago, nudge_needed }

Done criteria:
☐ Screenshot upload extracts item correctly
☐ Share handler works for text content
☐ Manual entry saves with correct tags
☐ Pre-purchase check returns correct duplicate result
☐ Consumables not flagged as duplicates

---

### Phase 8: Full Nudge System (12:00 PM – 3:00 PM)

Goal: Complete nudge flow works end-to-end.
      This is the core demo moment — must be bulletproof.

Steps:
1. Nudge decision engine (Claude Code):
   - POST /nudges/fire
   - Input: user_id, trigger_type, context
   - Logic:
     if budget_pct > 85 AND similar_item: tier = hard
     if budget_pct > 70 OR similar_item: tier = medium
     else: tier = light
   - Call Gemini for copy
   - Save nudge to MongoDB
   - Return nudge payload to frontend

2. Nudge response handler (Claude Code):
   - POST /nudges/respond
   - Input: nudge_id, response (paused|overridden)
   - Update nudge.user_response in MongoDB
   - If paused: increment streak counter
   - If overridden: reset streak (hard tier only)

3. Frontend nudge popup (Claude Code):
   - On Shop Check tap → call /nudges/fire
   - Receive nudge payload
   - Animate bottom sheet up
   - Show state-coloured popup with Gemini copy
   - Handle button taps → POST /nudges/respond
   - Toast: "Nice one! Streak: 5 days 🔥" on pause

4. Full flow test (THE DEMO PATH):
   Step 1: Set user spend to 78% in MongoDB
   Step 2: Add a past purchase (blue kurta)
   Step 3: Open Shop Check → tap Myntra
   Step 4: Upload screenshot of similar item
   Step 5: Verify nudge fires with correct copy
   Step 6: Tap "I'll wait" → verify streak increments
   Step 7: Check MongoDB → nudge logged correctly
   This entire flow must work perfectly before moving on.

Done criteria:
☐ Nudge fires correctly for all 3 trigger types
☐ Nudge tier logic works correctly
☐ Gemini copy is state-appropriate
☐ User response logged to MongoDB
☐ Streak increments on pause
☐ FULL DEMO PATH works end-to-end without error

---

### Phase 9: Security Checklist (3:00 PM – 5:00 PM)

Goal: Security checklist from PDF completed.
      No sensitive data exposed anywhere.

Steps:
1. Add security headers middleware (Claude Code):
   Paste into Claude Code:
   "Review my FastAPI app as a security specialist.
    Add: Content-Security-Policy, X-Frame-Options: DENY,
    X-Content-Type-Options: nosniff, HSTS, Referrer-Policy"

2. Add rate limiting (slowapi):
   - POST /nudges/fire: max 10/minute per user
   - POST /transactions/sync: max 2/minute per user
   - POST /auth/login: max 5/minute per IP

3. Input validation:
   - Budget amount: must be number, positive, max ₹10,00,000
   - Image upload: max 5MB, image types only
   - All string inputs: strip and sanitise

4. Key exposure check:
   Run: grep -r 'API_KEY\|SECRET\|mongodb\|fivetran'
        --include='*.js' --include='*.jsx' .
   Everything must come back empty in frontend files.

5. Add privacy policy at /privacy route
   Add terms of service at /terms route

Done criteria:
☐ All security headers present (verify in browser DevTools)
☐ Rate limiting tested (burst requests return 429)
☐ No API keys in any frontend file
☐ /privacy and /terms routes accessible
☐ Delete account flow works (all MongoDB data purged)

---

## Day 5 — Deploy + Polish

### Phase 10: Cloud Run Deployment (9:30 AM – 12:00 PM)

Goal: SpendSense is live on a public URL.
      Judges can open it from anywhere.

Steps:
1. Backend deployment (Google AI Studio → Cloud Run):
   - Create Dockerfile in backend/
   - One-click deploy from Google AI Studio
   - Set all .env variables as Cloud Run environment variables
   - Set min-instances: 1 (warm for demo day)
   - Test: curl https://[cloudrun-url]/health → 200 OK

2. Frontend deployment:
   - npm run build → creates /build folder
   - Deploy to Firebase Hosting or serve from Cloud Run
   - Update ALLOWED_ORIGINS in backend .env to live URL

3. Antigravity agent deployment:
   - Deploy agent to Google Cloud from Antigravity 2.0
   - Connect to live MongoDB URI
   - Connect to live Fivetran connector
   - Test scheduled sync trigger

4. End-to-end test on live URL:
   - Register new account on live URL
   - Complete onboarding
   - Trigger Fivetran sync
   - Verify wallet state appears
   - Trigger nudge → verify popup fires

Done criteria:
☐ Backend live on Cloud Run URL (returns 200)
☐ Frontend accessible on public URL
☐ Antigravity agent running in cloud
☐ Full flow works on live URL (not just localhost)
☐ PWA installs correctly from live URL on Android

---

### Phase 11: Monthly Report + Final Polish (12:00 PM – 5:00 PM)

Goal: Monthly report works. App is demo-ready.
      Every screen looks exactly as designed.

Steps:
1. Monthly report generation (Claude Code):
   - GET /report/current-month
   - Aggregate: transactions, nudges, purchases for current month
   - Calculate all metrics: nudges fired, paused, saved ₹
   - Generate Gemini insight text:
     "Generate a 1-sentence insight about this user's
      spending pattern this month: {data}"
   - Save to monthly_reports collection
   - Return full report to frontend

2. Report screen UI:
   - Render all metrics from API
   - Animated number count-up on enter
   - Share button → native share sheet

3. Final UI polish pass:
   - Every screen: check loading states show correctly
   - Every screen: check empty states show correctly
   - Every screen: check error states handle gracefully
   - All animations smooth on mobile
   - Test on actual Android Chrome (PWA install)

4. README.md (Claude Code generates):
   - Project description
   - Architecture diagram (text-based)
   - Setup instructions
   - Partner MCP integration explanation
   - Screenshots section

Done criteria:
☐ Monthly report generates with all metrics
☐ Report screen renders correctly
☐ All loading/empty/error states handled
☐ Animations smooth on actual Android device
☐ README.md complete and accurate

---

## Day 6 — Demo Video + Submission

### Phase 12: Demo Video (9:30 AM – 12:00 PM)

Goal: 3-minute demo video recorded and polished.

Script (memorise this):

```
0:00–0:30  THE PAIN
"Every month I'd reach the 25th with ₹800 left.
 Not because of one big purchase.
 Because of 47 small ones I didn't think about.
 I built SpendSense to fix that."

0:30–0:40  THE STACK
"SpendSense is an AI agent built on Google Antigravity
 with Gemini 3.5 Flash — powered by Fivetran MCP
 for real-time transaction data pipelines."

0:40–1:30  THE DEMO (main moment)
Show on phone:
- Open SpendSense → wallet in amber state (58% used)
- Tap Shop Check → select Myntra
- Nudge fires: "bestie, your closet called"
  Shows: similar kurta bought 12 days ago
  Shows: fashion budget 78% used
- Tap "I'll wait ✓"
- Streak increments: "5 days 🔥"

1:30–2:00  THE INTELLIGENCE
- Show screenshot upload → Gemini reads item
- Show duplicate detection in action
- Show 4 wallet states (change % in demo account)
- Show living wallet colour shift: amber → red

2:00–2:30  THE REPORT
- Open monthly report
- Show: 14 nudges fired, 9 paused, ₹4,200 saved
- "SpendSense proved its value in one month"

2:30–3:00  THE IMPACT
"400 million GenZ users in India face this exact problem.
 No existing app intercepts impulse spending before it happens.
 SpendSense does — using Gemini's behavioral reasoning
 and Fivetran's real-time data pipeline.
 This is what an AI agent that actually acts looks like."
```

Recording tips:
- Record on actual Android phone (PWA installed)
- Use screen record + voiceover
- One clean take — no jump cuts mid-demo
- Captions on for accessibility

### Phase 13: Devpost Submission (12:00 PM – 3:00 PM)

Steps:
1. Devpost project page:
   - Title: SpendSense — AI Agent That Stops Impulse Spending
   - Tagline: "The wallet that feels your financial health"
   - Partner track: Fivetran
   - GitHub URL: public repo link
   - Hosted URL: Cloud Run URL
   - Demo video: uploaded

2. Devpost description sections:
   - Inspiration: personal story (end of month ₹800 left)
   - What it does: 3 paragraphs from problem statement
   - How we built it: stack explanation, Fivetran MCP role
   - Challenges: mention honest technical challenges faced
   - Accomplishments: Living Wallet concept, Gemini Vision
   - What we learned: agent design patterns, MCP integration
   - What's next: Account Aggregator V2, Chrome extension

3. Final GitHub check:
   - LICENSE visible in About section ← required
   - README has screenshots
   - No .env committed
   - Clean commit history

Done criteria:
☐ Devpost submission complete and published
☐ GitHub repo public with LICENSE visible
☐ Hosted URL accessible and loads correctly
☐ Demo video uploaded and plays correctly
☐ Partner track selected: Fivetran
☐ All required Devpost fields filled

---

## Emergency Cuts (If Behind Schedule)

If Day 3 runs over — cut these, add to "What's next":
- Share button handler (keep screenshot only)
- Morning notifications (keep manual Shop Check only)
- Settings screen (hardcode notification time)

If Day 4 runs over — cut these:
- Manual entry for purchases (keep screenshot only)
- Monthly report auto-generation (show static demo data)

Never cut:
- Core nudge flow (this IS the demo)
- Living Wallet colour states (this IS the wow moment)
- Fivetran MCP integration (this IS the partner track)
- Duplicate detection (this IS the unique feature)

---

## Claude Code Prompts — Ready To Use

### Day 1 Setup
"Set up a FastAPI project with the folder structure in my TRD document.
 Create main.py, requirements.txt, Dockerfile, and .gitignore.
 Install all packages from the TRD key libraries section."

### Day 1 Auth
"Build JWT authentication for my FastAPI app using python-jose.
 Create POST /auth/register and POST /auth/login endpoints.
 Hash passwords with bcrypt. Return JWT token on success.
 Protect all other routes with JWT middleware."

### Day 2 MongoDB
"Create MongoDB collections and indexes for my SpendSense app.
 Use the exact schema from my Backend Schema document.
 Create a mongodb.py service file with connection and helper functions."

### Day 3 Gemini
"Build a Gemini service that generates GenZ nudge notifications.
 Use this prompt template: [paste from Phase 5 above]
 Return parsed JSON with title, body, tag fields.
 Handle API errors gracefully with a fallback message."

### Day 4 Security
"Review my entire FastAPI codebase as a security specialist.
 Add security headers middleware.
 Add rate limiting with slowapi.
 Check for any exposed API keys.
 Validate all input fields."

---

*Document version: 1.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*
