# Document 03 — App Flow: Navigation & User Journey Map
# SpendSense

---

## All Pages / Screens

| Route | Screen Name | Purpose |
|---|---|---|
| `/` | Landing / Welcome | First screen new visitor sees |
| `/register` | Register | Create username + password |
| `/login` | Login | Return user authentication |
| `/onboarding/budget` | Budget Setup | Set master + category budgets |
| `/onboarding/connect` | Connect Data | Upload CSV or Google Pay export |
| `/onboarding/success` | Setup Complete | Confirmation + go to dashboard |
| `/dashboard` | Main Dashboard | Budget bar, transactions, nudges, streak |
| `/add-purchase` | Add Purchase | Screenshot / Share / Manual options |
| `/check-before-buy` | Pre-Purchase Check | Screenshot product → Gemini checks history |
| `/nudge` | Nudge Popup | Full-screen overlay nudge card |
| `/report` | Monthly Report | End-of-month savings summary |
| `/settings` | Settings | Budget edit, data refresh, delete account |
| `/privacy` | Privacy Policy | Legal requirement |
| `/terms` | Terms of Service | Legal requirement |

---

## Navigation Structure

**Logged-out users:** Top navbar with Logo + Login + Register buttons

**Logged-in users:** Bottom tab navigation (mobile-first)
```
[ 🏠 Dashboard ]  [ 🛍️ Shop Check ]  [ 📊 Report ]  [ ⚙️ Settings ]
```

Nudge popup appears as full-screen overlay above any screen —
slides up from bottom when triggered. Not a tab.

---

## First Screen — New Visitor

User lands on `/` — Welcome screen.
Shows: SpendSense logo, tagline, one-line problem statement,
social proof: "Join GenZ Indians saving more every month"
Two buttons: [Get Started — it's free] [I already have an account]

---

## Auth Flow

```
/register
  → username + password fields
  → tap [Create Account]
  → JWT token issued
  → redirect to /onboarding/budget

/login
  → username + password fields
  → tap [Login]
  → JWT token issued
  → if onboarding complete → /dashboard
  → if onboarding incomplete → /onboarding/budget
```

---

## Onboarding Flow (One-time setup)

```
Step 1: /onboarding/budget
  → User enters master monthly budget (e.g. ₹15,000)
  → Optional: expand to set category budgets:
      Food & Groceries: ₹_____
      Shopping & Fashion: ₹_____
      Electronics: ₹_____
      Others: ₹_____
  → Tap [Set My Budget] → /onboarding/connect

Step 2: /onboarding/connect
  → Explanation: "Connect your spending data so 
    SpendSense can track your budget position"
  → Two options:
      [Upload UPI / Bank CSV]
      [Connect Google Pay Export]
  
  Path A: Upload CSV
    → Drag and drop or browse CSV file
    → Fivetran connector processes file
    → Loading: "Reading your transactions..."
    → Shows count: "142 transactions imported ✓"
    → Tap [Continue] → /onboarding/success

  Path B: Google Pay Export
    → Instructions: how to export GPay CSV
    → Same upload flow as Path A

Step 3: /onboarding/success
  → "SpendSense is ready! 🎉"
  → Summary: budget set + transactions imported
  → Quick tip shown:
    "Add your recent purchases so SpendSense
     remembers what you've already bought"
  → [Add a Recent Purchase] or [Go to Dashboard]
```

---

## Layer 1 — Morning Proactive Notification (Automatic)

```
Every morning at 9 AM — PWA push notification fires:

"Good morning! Your SpendSense update ☀️
 Budget used: ₹8,400 of ₹15,000 (56%)
 Last fashion purchase: Blue Kurta — 12 days ago
 Tap to see full position before you shop"

User taps notification
  → SpendSense opens to /dashboard
  → Full budget position visible immediately
  → If high risk detected → nudge overlay fires automatically
```

---

## Layer 2 — Pre-Shop Quick Check (One tap)

```
User is about to open a shopping app
  → Opens SpendSense first
  → Taps [🛍️ Shop Check] tab → /check-before-buy

  → Screen shows quick app selector:
    [Myntra] [Amazon] [Flipkart]
    [Zepto]  [Blinkit] [Swiggy]
    [Other]

  → User taps the app they're about to open
  → Gemini instantly pulls:
      Last purchase on that platform
      Current budget position
      Category budget remaining
      Purchase frequency this week

  → POPUP FIRES immediately:

  ┌─────────────────────────────────────┐
  │  🛑 SpendSense Check                │
  │                                     │
  │  Before you open Myntra             │
  │                                     │
  │  Last purchase here:                │
  │  👗 Blue Printed Kurta              │
  │     ₹899 · 12 days ago              │
  │                                     │
  │  This month's budget:               │
  │  ████████░░  78% used               │
  │  ₹11,700 of ₹15,000                 │
  │                                     │
  │  Fashion specifically:              │
  │  ██████████  94% used               │
  │  ₹2,820 of ₹3,000                   │
  │                                     │
  │  💡 You're close to your limit.     │
  │                                     │
  │  [I'll skip today ✓] [Open anyway]  │
  └─────────────────────────────────────┘

  User taps [I'll skip today ✓]
    → Nudge logged as PAUSED
    → Streak incremented
    → Toast: "Nice one! Streak: 5 days 🔥"

  User taps [Open anyway]
    → Nudge logged as OVERRIDDEN
    → No judgment — returns to dashboard
    → Streak resets if hard tier nudge
```

---

## Layer 3 — Pre-Purchase Specific Item Check

```
User is already browsing Myntra
  → Sees something they like
  → Screenshots the product page
  → Opens SpendSense → [🛍️ Shop Check] tab
  → Taps [Check a specific item]
  → Uploads screenshot

  → Gemini Vision reads product:
      Item: Floral Ethnic Top
      Price: ₹1,200
      Platform: Myntra (detected from screenshot)

  → Gemini checks purchase history:
      "Similar item found: Blue Printed Kurta
       purchased 12 days ago — ₹899"

  → POPUP FIRES:
  ┌─────────────────────────────────────┐
  │  ⚠️  Similar item in your history   │
  │                                     │
  │  You're checking:                   │
  │  🌸 Floral Ethnic Top — ₹1,200      │
  │                                     │
  │  You already bought:                │
  │  👗 Blue Printed Kurta — ₹899       │
  │     Just 12 days ago                │
  │                                     │
  │  Fashion budget:                    │
  │  ██████████  94% used               │
  │                                     │
  │  [Skip this one ✓] [I still want it]│
  └─────────────────────────────────────┘

  If no similar item found:
  ┌─────────────────────────────────────┐
  │  ✅ Looks good!                     │
  │                                     │
  │  Nothing similar in your history.   │
  │  Budget remaining: ₹3,600           │
  │  This item: ₹1,200                  │
  │                                     │
  │  You're within budget. Go for it!   │
  └─────────────────────────────────────┘
```

---

## Purchase Capture Flow (Add Purchase)

```
User taps [+ Add Purchase] on dashboard
  → /add-purchase screen

  Three options:

  📸 Upload Screenshot (Primary)
    → User uploads order confirmation screenshot
    → Gemini Vision extracts:
        Item name, size, colour, price,
        platform, date, order number
    → Preview shown: "Is this correct?"
    → User confirms → stored ✓
    → Toast: "Added to your purchase history ✓"

  ↗️ Share from App (Primary)
    → Instructions: "Go to your order confirmation
      in any app → tap Share → select SpendSense"
    → SpendSense receives shared content
    → Gemini processes:
        If rich text → extracts details directly
        If URL only → attempts fetch
        If login required → prompts screenshot
    → Stored ✓

  ✏️ Add Manually (Fallback)
    → Simple 4-field form:
        What did you buy? [text field]
        Where?           [platform dropdown]
        How much?        [₹ amount]
        Category?        [dropdown]
    → Tap [Save] → stored ✓
    → Takes under 20 seconds
```

---

## Dashboard Flow

```
User opens SpendSense → /dashboard

Screen shows:
  ┌─────────────────────────────────┐
  │  Hi Akshitha! 👋                │
  │  June 2026                      │
  │                                 │
  │  Monthly Budget                 │
  │  ████████░░ 78% used            │
  │  ₹11,700 of ₹15,000             │
  │                                 │
  │  Category Breakdown:            │
  │  🍕 Food      ██░░  45%         │
  │  👗 Fashion   ████  94%  ⚠️     │
  │  📱 Electronics ░░  12%         │
  │                                 │
  │  🔥 Streak: 5 days              │
  │                                 │
  │  Recent Purchases:              │
  │  Blue Kurta · Myntra · ₹899     │
  │  Vegetables · Zepto  · ₹340     │
  │  Headphones · Amazon · ₹1,299   │
  │                                 │
  │  [+ Add Purchase]               │
  │  [🛍️ Shop Check]                │
  └─────────────────────────────────┘

If Fashion budget > 90%:
  → Warning chip shown on category bar
  → Tapping chip opens nudge context popup
```

---

## Monthly Report Flow

```
User taps [📊 Report] tab → /report

Report card renders:
  ┌─────────────────────────────────┐
  │  June 2026 Report 📊            │
  │                                 │
  │  🛑 Nudges fired: 14            │
  │  ✅ You paused: 9 (64%)         │
  │  💰 Estimated saved: ₹4,200     │
  │                                 │
  │  Budget used: 82% of ₹15,000   │
  │  🔥 Best streak: 7 days         │
  │                                 │
  │  Top impulse category:          │
  │  👗 Fashion (8 of 14 nudges)    │
  │                                 │
  │  [Share Report 📤]              │
  └─────────────────────────────────┘

Tap [Share Report]
  → Native share sheet opens
  → Screenshot of report card shared

If early in month (< 10 days):
  → "Your June report is building...
     So far: ₹X not spent 💪
     Keep going!"
```

---

## Settings Flow

```
/settings
  → Edit master budget → updates MongoDB
  → Edit category budgets → updates MongoDB
  → Manual data refresh → triggers Fivetran sync
  → Notification time → change morning alert time
  → View privacy policy → /privacy
  → View terms → /terms
  → Delete all my data
      → confirmation modal
      → confirms → deletes all MongoDB records
      → redirects to /register
  → Logout → clears JWT → redirects to /
```

---

## Empty States

| Screen | Empty State |
|---|---|
| Dashboard — no purchases | "No purchases logged yet. Add your first one!" + [+ Add Purchase] |
| Dashboard — no nudges | "No nudges yet — you're doing great! 🎉" |
| Shop Check — no history | "No purchase history for this app yet. Add a purchase first." |
| Report — no data | "Your report builds as you use SpendSense. Keep going!" |
| Transaction feed | "No transactions yet. Upload your bank CSV to get started." |

---

## Error States

| Scenario | What user sees |
|---|---|
| Fivetran sync fails | Toast: "Sync failed. Try again." + [Retry] |
| Gemini Vision can't read screenshot | "Couldn't read this image. Try a clearer screenshot or add manually." |
| Gemini API timeout | "Analysis delayed. Check dashboard for spending summary." |
| MongoDB error | "Unable to load data. Please refresh." |
| Session expired | Redirect /login: "Session expired. Please log in again." |
| CSV format invalid | "File format not supported. Export as CSV from your bank app." |
| Share content unreadable | "Couldn't read shared content. Try uploading a screenshot instead." |

---

## Loading States

| Action | Loading indicator |
|---|---|
| Dashboard load | Skeleton shimmer cards |
| Fivetran sync | Spinner + "Syncing transactions..." |
| Gemini Vision processing | Animated scan effect + "Reading your order..." |
| Shop Check analysis | Spinner + "Checking your history..." |
| Report generating | Spinner + "Building your June report..." |

---

## Redirect Logic

| Action | Redirects to |
|---|---|
| After register | /onboarding/budget |
| After login (complete) | /dashboard |
| After login (incomplete) | /onboarding/budget |
| After logout | / |
| After data delete | /register |
| After onboarding | /dashboard |
| Unauthenticated → /dashboard | /login |

---

## Three-Layer Protection Summary

| Layer | Trigger | Method | Automatic? |
|---|---|---|---|
| Layer 1: Morning Alert | 9 AM daily | PWA push notification | ✅ Yes |
| Layer 2: Pre-Shop Check | Before opening app | [Shop Check] tab + app selector | One tap |
| Layer 3: Specific Item | During browsing | Screenshot upload to SpendSense | One tap |

---

*Document version: 2.0 | Date: June 2026 | Hackathon: Google Cloud Agent Builder*
