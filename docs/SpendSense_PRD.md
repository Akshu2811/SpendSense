# Document 01 — PRD: Product Requirements Document
# SpendSense

---

## App Name
**SpendSense**

## Tagline
*Your money's guardian — stops impulse buys before they happen.*

---

## The Problem

GenZ salaried professionals in Indian metros consistently reach end-of-month 
with depleted savings — not from big purchases, but from accumulated impulse 
buys across quick commerce (Zepto, Blinkit, Swiggy) and e-commerce apps 
(Myntra, Amazon, Flipkart), driven by boredom, habit, and zero real-time 
awareness.

No existing tool intercepts them at the moment of temptation with enough 
context to make them pause. Expense trackers only tell you what you already 
spent. Neobank dashboards are locked to one bank. Nothing reasons over your 
behavior and acts before damage is done.

---

## Target User

**Primary persona:** Akshitha, 24, software professional in Hyderabad.
Earns a monthly salary, pays via UPI and credit card across 5+ apps daily.
Hits end of month with less than expected savings — every month. Knows she 
overspends but has no real-time signal to stop her. Uses her phone for 90% 
of all purchases across Myntra, Zepto, Amazon, and Blinkit.

---

## Core Value Proposition

SpendSense is the first AI agent that intercepts impulse purchases **before** 
they happen — not after. It builds a detailed purchase memory from your order 
history using Gemini Vision, monitors cross-platform spending via a Fivetran 
data pipeline, and fires a calibrated nudge the moment you're about to repeat 
a purchase or breach your budget. It doesn't just track. It acts.

What makes it different from Jupiter, Monzo, or Walnut:
- Cross-platform: sees ALL spending regardless of bank or payment method
- Item-level memory: knows exactly what you bought, not just how much
- Pre-purchase: fires before you spend, not after damage is done
- Agent reasoning: Gemini analyses behavioral patterns, not just numbers

---

## How Purchase Data is Captured

SpendSense uses three methods to build your purchase memory.
All methods are privacy-safe — no Gmail access, no bank passwords, no OAuth.

### Method 1 — Screenshot Upload (Primary)
User takes a screenshot of any order confirmation screen.
SpendSense uses Gemini Vision to extract:
item name, size, colour, price, platform, date.
Works for every app on every phone — universal.

### Method 2 — Share Button (Primary)
User taps the native Share button inside any app (Myntra, Amazon, Zepto etc.)
and selects SpendSense from the share sheet.
SpendSense receives the shared content and Gemini extracts order details.
If the shared URL requires app login to view — SpendSense prompts the user
to use the screenshot method instead.

### Method 3 — Manual Quick-Add (Fallback)
User enters purchase details manually via a simple 4-field form:
item description, platform, amount, category.
Takes under 20 seconds. Available as fallback at any time.

### Budget & Transaction Tracking (via Fivetran MCP)
Separate from item-level capture — for overall budget monitoring.
User uploads UPI/bank CSV or connects Google Pay export.
Fivetran pipeline syncs transaction data into MongoDB.
This powers: budget progress bars, spending pattern detection,
monthly report, and overall financial position awareness.

---

## Core Features — Must Have (MVP)

### 1. Onboarding & Budget Setup
- User sets a master monthly budget (e.g. ₹15,000)
- Optional: breakdown into category budgets
  (Food, Dining & Delivery / Shopping & Fashion / Electronics & Tech / Entertainment & Subscriptions / Health & Lifestyle / Others)
- User connects transaction data via:
  - Upload UPI/bank CSV export
  - Connect Google Pay transaction export
- User adds first purchases via screenshot, share, or manual entry
- Fivetran MCP pipeline ingests and syncs transaction data into MongoDB

**Data Refresh Policy:**
- CSV and manual entry users trigger refresh from dashboard
- Google Pay export users get automatic daily sync via Fivetran scheduler
- Full real-time sync across all Indian banks planned for V2
  via RBI's Account Aggregator framework

### 2. Purchase Memory — Item Level (Gemini Vision)
- Screenshot upload: Gemini Vision reads order confirmation image
  and extracts item name, size, colour, price, platform, date
- Share button: user shares from any app → Gemini processes content
- Manual entry: 4-field quick-add form as fallback
- All purchases stored in MongoDB purchase history (last 60 days active)
- Smart categorisation: consumable vs durable
  (groceries never flagged as duplicates — only lifestyle/fashion/electronics)

### 3. Smart Transaction Sync (Fivetran MCP)
- Fivetran connector pulls latest transactions on trigger or schedule
- Agent checks data freshness before every analysis
- Supports all payment methods: UPI, credit card, debit card, BNPL
- Powers budget tracking — separate from item-level purchase memory

### 4. Gemini-Powered Behavioral Analysis
Detects three risk signals:
- **Budget breach risk:** spending approaching or over budget threshold
- **Duplicate purchase:** similar item bought in last 60 days
  (consumable vs durable logic — groceries/essentials never flagged)
- **Frequency pattern:** high purchase frequency in short window

Classifies every detected risk into three nudge tiers:
- **Light:** informational — "You've spent ₹3,200 on fashion this week"
- **Medium:** contextual warning — "You bought something similar 12 days ago"
- **Hard:** cooling-off nudge — "Come back in 10 mins if you still want this"

### 5. Pre-Purchase Check Flow
User is about to buy something on any app.
User screenshots the product page OR shares it to SpendSense.
Gemini checks against purchase history:
- Similar item found → nudge fires with full context
- Budget at risk → nudge fires with spending position
- All clear → "Looks good — nothing similar found ✓"

### 6. Nudge Popup System
- Attractive, mobile-first overlay card
- Shows: item similarity context + budget used % + specific reason
- Two action buttons: [Skip anyway] [I'll wait ✓]
- User response logged for monthly report
- PWA push notification on Android Chrome for proactive alerts

### 7. Spending Dashboard
- Real-time budget progress bar (master + category breakdown)
- Recent transaction feed with category tags
- Active nudge history — what fired, what the user chose
- Current month spending streak (days without impulse override)
- Savings goal progress indicator
- [Add Purchase] button — screenshot / share / manual options

### 8. Monthly Savings Report
Auto-generated at month end (or on demand). Displays:
- Total nudges fired vs paused
- Estimated money not spent (₹ saved via pauses)
- Budget utilisation % vs goal
- Streak count — consecutive impulse-free days
- "Your biggest impulse category this month: Fashion"

---

## Nice to Have — V2 / If Time on Day 4

### Spending Streak (Gamified)
- Track consecutive days without an impulse override
- Visual streak counter on dashboard (Duolingo-style flame)
- Streak resets when user taps "Skip anyway" on a hard nudge
- Milestone notifications: "7-day streak! You saved ₹1,200 this week"

---

## Explicitly Out of Scope (This Version)

- Gmail access or OAuth of any kind — privacy boundary
- SMS parsing for purchase capture — order SMS has no item details
- Friends / social comparison features — V2
- Native Android or iOS app — PWA covers demo needs
- Direct bank API integration — CSV upload for now
- Automated purchase blocking — nudges only, never forces
- Investment or SIP recommendations — spending guard only
- International currencies — India/INR only
- Admin dashboard or analytics panel
- Chrome extension for automatic cart detection — V2

---

## User Stories

**Onboarding**
- As a new user, I want to set my monthly budget and connect my transaction 
  data so that SpendSense can start tracking my spending immediately.
- As a user, I want to add my recent purchases via screenshot, share button, 
  or manual entry so that SpendSense builds my purchase memory from day one.

**Purchase Capture**
- As a user who just bought something on Myntra, I want to screenshot my 
  order confirmation and upload it to SpendSense so it remembers exactly 
  what I bought.
- As a user, I want to tap Share inside any shopping app and select 
  SpendSense so my purchase is logged without switching apps manually.

**Pre-Purchase Check**
- As a user browsing Myntra, I want to screenshot a product I'm considering 
  and check it against my history so I know if I've bought something similar.
- As a user, I want SpendSense to tell me specifically why it's flagging a 
  purchase — budget, duplicate, or frequency — so I can make an informed 
  decision.
- As a user, I want to tap "I'll wait" or "Skip anyway" so I feel in control,
  not blocked.

**Dashboard**
- As a user, I want to see my budget progress in real time so I always know 
  where I stand without opening a bank app.
- As a user, I want to see my spending streak so I feel motivated to maintain
  impulse-free days.

**Monthly Report**
- As a user at end of month, I want to see how much money SpendSense helped 
  me not spend so I can see the agent's real impact.
- As a user, I want to know which category triggered the most nudges so I 
  understand my spending patterns better.

**Privacy & Trust**
- As a user, I want my data stored securely without SpendSense ever accessing
  my Gmail, SMS, or bank passwords.
- As a user, I want to be able to delete all my data at any time.

---

## Success Metrics

### For the Hackathon Demo
- Full agent flow runs end-to-end without error:
  Screenshot/Share → Gemini extracts → stored → pre-purchase check → 
  nudge fires → response logged
- Nudge popup renders correctly on mobile screen recording
- Monthly report generates with all three metrics populated
- Demo video tells a complete story in under 3 minutes

### For Real-World Validation (Post-Hackathon)
- User reaches end of month with ≥ target savings amount
- At least 50% of nudges result in "I'll wait" response (pause rate)
- Average budget utilisation drops below 90% vs pre-SpendSense baseline
- User maintains a 7-day+ spending streak within first month

---

## Judging Criteria Alignment

| Criterion | How SpendSense addresses it |
|---|---|
| Technological Implementation | Fivetran MCP pipeline + Gemini Vision + Gemini 3.5 Flash behavioral reasoning + Antigravity 2.0 orchestration — non-trivial multi-step agent |
| Design | Mobile-first PWA, Gemini Vision screenshot flow, attractive nudge popup, gamified streak — UX is core to the product |
| Potential Impact | 400M+ GenZ users in India facing this exact pain. Financial wellness at scale. |
| Quality of Idea | No existing tool does pre-purchase behavioral interception with item-level memory. First of its kind as an agent. |

---

## Competitive Differentiation

| Competitor | What they do | SpendSense advantage |
|---|---|---|
| Jupiter / Fi Money | Dashboard + alerts for one bank | Cross-platform, pre-purchase, item-level |
| Walnut | SMS transaction tracking | Item-level via Vision, not just amounts |
| Monzo | Neobank with spending insights | Works with any Indian bank/app |
| Stop Impulse Spending | Manual no-spend log | Fully intelligent, no manual tracking |

---

*Document version: 2.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*

---

## Core Idea — The One Thing SpendSense Does

> SpendSense stops you from spending impulsively — across every app,
> every category, every rupee — before the damage is done.

Every feature traces back to this:

| Feature | Why it exists |
|---|---|
| Fivetran pipeline | So the agent knows exactly what you've spent |
| Gemini Vision | So the agent knows exactly what you've bought |
| 6 spending categories | So no impulse spend escapes detection |
| 3 nudge tiers | So the intervention matches the risk level |
| GenZ notifications | So you actually listen to the warning |
| Monthly report | So you see proof it worked |

### The 6 Spending Categories

| Category | Apps covered |
|---|---|
| Food, Dining & Delivery | Swiggy, Zomato, Blinkit, Zepto, BB Daily |
| Shopping & Fashion | Myntra, Ajio, Meesho, Nykaa, Amazon Fashion |
| Electronics & Tech | Amazon, Flipkart, Croma, Reliance Digital |
| Entertainment & Subscriptions | Netflix, Spotify, BookMyShow, Steam |
| Health & Lifestyle | PharmEasy, 1mg, Cult.fit, Minimalist |
| Others | Any UPI merchant not in above categories |

### Cross-Category Intelligence (Gemini's superpower)

Gemini reasons across all 6 categories simultaneously:

"You've hit impulse spends across 3 categories this week:
 Food delivery: ₹1,800 (90% of budget)
 Fashion: ₹2,340 (78% of budget)
 Entertainment: ₹890 (89% of budget)
 Total impulse risk: HIGH — 84% overall budget used, 16 days left"

### Key Pitch Lines

Devpost: "SpendSense — AI agent that stops impulse spending before it happens"
Demo opener: "Every month I'd reach the 25th with ₹800 left. Not because
              of one big purchase. Because of 47 small ones I didn't think
              about. SpendSense fixes that."
Judge answer: "It's not a tracker. Trackers show you what you already spent.
               SpendSense stops you before you spend it."
