# Document 04 — UI/UX Design Brief
# SpendSense

---

## Core Design Philosophy

SpendSense must feel like a mood ring for your money — not a banking app.
The entire visual experience IS the data. Users understand their financial
health from the colour and atmosphere alone, before reading a single number.

Three words that define the aesthetic:
**Alive. Emotional. Reactive.**

---

## The Living Wallet Concept — Never Been Done Before

SpendSense's entire UI shifts dynamically based on the user's current
wallet state. The background, orb colour, mood text, nudge tone, and
notification personality ALL change in real time as spending increases.

Think of it like a mood ring for money:
- The app doesn't SHOW you your financial health
- The app IS your financial health — visually

### The 4 Wallet States

| State | Trigger | Colour | Mood Text | Feeling |
|---|---|---|---|---|
| Calm | 0–40% spent | Ocean Blue #00B4D8 | "breathing easy ✦" | Sunday morning |
| Aware | 40–70% spent | Warm Amber #F77F00 | "heads up, bestie 👀" | Gentle alert |
| Urgent | 70–85% spent | Coral Red #E63946 | "feeling the heat 🌶️" | Wallet sweating |
| Crisis | 85%+ spent | Electric Violet #9B5DE5 | "wallet in crisis 💀" | Emergency mode |

### What Changes Per State

Every state transition shifts ALL of the following simultaneously:

```
BACKGROUND COLOUR    →  Deep dark tone matching state colour
AMBIENT ORBS         →  Large glowing blobs shift colour + intensity
                         Bigger when healthy, shrink when critical
MOOD TEXT            →  Human language, not percentage labels
NUDGE POPUP          →  Colour + tone + emoji match current state
NOTIFICATIONS        →  Morning alert colour matches wallet state
BUTTON ACCENTS       →  Primary CTA colour matches state
```

### State Transitions

Transitions are smooth — 1.5s CSS ease transition between states.
The app never jumps between states. It breathes and flows.
Spending feels consequential, not clinical.

---

## How The Living Wallet Is Built — Google Tools Only

### Where Colours Are Stored
MongoDB Atlas stores the current wallet state string:
"calm" | "aware" | "urgent" | "crisis"
Recalculated after every Fivetran sync.

### Where Logic Runs
Google Antigravity 2.0 agent:
- Reads latest spend % from MongoDB after Fivetran sync
- Gemini 3.5 Flash makes a judgment — not just a calculation:
  "Is this user calm, aware, urgent, or in crisis right now?"
- Saves state string to MongoDB
- Frontend reads: GET /wallet-state → returns state string

### Where UI Is Built
Google Stitch generates all components.
Each state is a CSS class with colour variables:

```css
.state-calm   { --bg: #050D1A; --orb: #00B4D8; --accent: #4FC3F7; }
.state-aware  { --bg: #120D05; --orb: #F77F00; --accent: #FFB347; }
.state-urgent { --bg: #150805; --orb: #E63946; --accent: #FF7043; }
.state-crisis { --bg: #0D0514; --orb: #9B5DE5; --accent: #CE93D8; }
```

JavaScript reads state from API → applies class → CSS handles the rest.

### The Gemini Judgment Layer

```
Fivetran syncs → Gemini reads:
"₹11,850 of ₹15,000 spent (79%)
 Fashion at 94% — multiple categories critical"
        ↓
Gemini outputs: STATE = "urgent"
        ↓
Frontend applies coral red atmosphere
        ↓
User opens app → feels urgency before
reading a single number
```

### Build Flow in Stitch

Step 1: Open Google Stitch
        Describe: "A dark mobile app dashboard with a large
        glowing orb in the center that changes colour based
        on a state variable. 4 states: calm=blue, aware=amber,
        urgent=red, crisis=violet. Background shifts smoothly
        with each state over 1.5 seconds."

Step 2: Stitch generates the React component

Step 3: Export to Firebase Studio

Step 4: Claude Code wires state variable to FastAPI endpoint

Step 5: Every Fivetran sync → Gemini recalculates →
        state updates → frontend colour shifts automatically

---

## Screen-By-Screen Design

### Dashboard (/dashboard)
Primary screen. The Living Wallet is the hero element.

Layout (top to bottom):
- Status bar
- "your wallet is" label (10px, muted)
- THE LIVING AURA: Large breathing orb (140px)
  Centre shows: spend percentage (32px light weight)
  Below orb: mood text in state accent colour
- Spent / Left row (two columns, separated by thin line)
- Screen divider (40px wide, 1px, very subtle)
- Category pills horizontal scroll (6 categories, colour-coded)
- Transaction feed (last 5 items, icon + name + date + amount)
- Streak bar (flame icon + days + streak count)
- Bottom navigation (4 tabs)
- Floating [+ Add Purchase] button (coral, bottom right)

### The Living Aura (Core Component)
Not a progress bar. A breathing, morphing blob.

```
Structure:
- Outer glow:   Large blurred circle behind orb (filter:blur 20px)
- Main blob:    Radial gradient circle, state colour
- Inner text:   Percentage (32px, weight 300) + "spent" label
- Mood text:    Below orb, state accent colour, 11px
```

Animations:
- Orb pulses gently (scale 1.0 → 1.03 → 1.0, 3s loop)
- On state change: smooth colour transition 1.5s ease
- On new transaction: brief orb pulse (scale 1.0 → 1.08 → 1.0)

### Nudge Popup (/nudge)
Bottom sheet. Slides up from bottom (0.3s ease-out).
Top 24px radius corners only. Rest is straight.

Structure (inside sheet):
- Drag pill (36x4px, rounded, rgba white)
- Nudge tag chip (emoji + text, state colour background)
- Large emoji / character (40px, centred)
- Title (15px, weight 500, white, centred)
- Body copy (11px, muted, centred, Gemini-generated)
- Context block (spend % + mini progress bar, state colour)
- Two buttons: [skip anyway] glass button | [i'll wait ✓] solid

Nudge popup also changes per state:
```
Calm state:   Blue tone, gentle emoji 😌, soft language
Aware state:  Amber tone, thinking emoji 🤔, pointed language
Urgent state: Red tone, worried emoji 😬, dramatic language
Crisis state: Violet tone, shocked emoji 😱, unhinged language
```

### Shop Check (/check-before-buy)
App grid: 3x2 grid of major shopping apps
(Myntra, Amazon, Flipkart, Zepto, Blinkit, Swiggy + Other)
Tap app → instant Gemini analysis → popup fires

Second option: [Check a specific item]
→ Screenshot upload → Gemini Vision checks purchase history
→ If similar found: nudge fires with specific comparison
→ If clear: "looks good — nothing similar found ✓"

### Add Purchase (/add-purchase)
Three large options with icons:
📸 Upload Screenshot → Gemini Vision extracts item details
↗️ Share from App → Receives shared content, Gemini processes
✏️ Add Manually → 4-field form (item, platform, amount, category)

### Monthly Report (/report)
Card-based. Same dark atmosphere as dashboard.

Header: "june 2026 / your month, honestly."
Three stat cards: nudges fired / times paused / best streak
Saved card: large ₹ amount in state accent colour + sparkle icon
Budget bar: horizontal, state gradient colour
Insight card: "top impulse zone: fashion (8 of 14 nudges)"
Share button: native share sheet (screenshot of report card)

---

## Notification Design

All notifications use Gemini-generated copy.
Copy tone and colour match current wallet state.

### Notification Personality Rules
- Never shame — always roast with love
- Reference real Indian GenZ life (maggi, zepto, "the math")
- Tone shifts with state: gentle → funny → dramatic → unhinged
- Always include real specific numbers
- Fresh copy every time — Gemini generates, never repeats in 7 days

### Sample Notifications Per State

CALM (blue):
Title: "good morning, financially stable human"
Body:  "56% budget used. it's giving responsible adult energy."

AWARE (amber):
Title: "going to myntra again? bold choice."
Body:  "you bought something there 12 days ago. your wardrobe remembers."

URGENT (red):
Title: "the math is not mathing bestie"
Body:  "₹11,850 gone. 16 days left in june. we need to talk."

CRISIS (violet):
Title: "okay so june was a journey"
Body:  "91% budget gone. surviving on maggi and hope. do NOT open myntra."

---

## Animation Specification

| Interaction | Animation |
|---|---|
| State change | Background + orb colour: 1.5s ease transition |
| Orb idle | Scale 1.0→1.03→1.0, loop 3s, ease-in-out |
| New transaction | Orb pulse: 1.0→1.08→1.0, 0.4s |
| Nudge appears | Bottom sheet slides up: 0.3s ease-out |
| "I'll wait" tap | Green flash + streak +1 toast (0.3s) |
| Budget bar load | Fill left to right: 0.6s ease-in-out |
| State numbers | Count up from 0 on screen enter |
| Streak milestone | Orb pulses 3x rapidly + toast notification |

---

## Component Style Guide

### Colours
Background:  State-dependent (see 4 states above)
Cards:       rgba(255,255,255,0.07) glass + 0.5px white border
Text:        White #FFFFFF (primary) / rgba(255,255,255,0.5) (muted)
Success:     #4ECCA3 (savings achieved, streak, positive)

### Cards
Background: rgba(255,255,255,0.07)
Border: 0.5px solid rgba(255,255,255,0.12)
Border-radius: 16px
Backdrop-filter: blur(12px)

### Typography
Font: System default (SF Pro on iOS, Roboto on Android)
Hero number: 32px, weight 300 (light — feels elegant not heavy)
Screen titles: 20px, weight 400
Card titles: 15px, weight 500
Body: 11–12px, weight 400
Labels: 9–10px, weight 500, letter-spacing 0.05em

### Buttons
Primary: Solid state-accent colour, white text, 14px radius, 48px height
Secondary: Glass (rgba white 0.07) + border, muted text
Destructive: rgba red 0.2 background

### Category Colours
Food & Delivery:        #FF6B4A (coral orange)
Shopping & Fashion:     #A89CF0 (soft purple)
Electronics & Tech:     #89B4FF (sky blue)
Entertainment & Subs:   #F15BB5 (hot pink)
Health & Lifestyle:     #4ECCA3 (mint green)
Others:                 #888780 (warm gray)

---

## Design Tool Workflow

```
Google Stitch
  → Describe each screen in plain English
  → Generates React + Tailwind components
  → All 4 state colour classes included
        ↓
Firebase Studio
  → Review exported components
  → Minor adjustments
        ↓
Claude Code
  → Wire state API endpoint
  → Connect Gemini state logic
  → Add animations and transitions
        ↓
Google Cloud Run
  → Deploy as PWA
  → Manifest + service worker for install
```

---

## What SpendSense Should Never Look Like

- A bank app (no navy blue, no formal serif, no security badges)
- A diet app (no guilt-inducing design, no red warning triangles)
- A generic SaaS dashboard (no data tables, no sidebars, no grids)
- A flat design app (no 2020-era minimalism — everything has depth)
- A light mode fintech app (SpendSense is dark-first, always)

---

## Reference Concept

Closest design inspiration: Tide Guide (2026 Apple Design Award winner)
Their principle: the app palette changes to match the colour of the sky.
SpendSense principle: the app atmosphere changes to match wallet health.
Same concept. Different domain. Never done in Indian fintech.

---

*Document version: 2.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*
