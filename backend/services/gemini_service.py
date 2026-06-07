import asyncio
import base64
import json
import logging
import os
import re
from datetime import datetime, timezone, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_raw_model = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash")
# Strip "models/" prefix — we add it in the URL
GEMINI_MODEL = _raw_model.removeprefix("models/")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _gemini_url() -> str:
    return f"{BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from Gemini response text."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find the outermost {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON object found in Gemini response: {text[:200]!r}")


def _get_text(response: dict) -> str:
    """Extract the text content from a Gemini API response.

    Handles standard and thinking-model response shapes:
    - Standard: candidates[0].content.parts[0].text
    - Thinking:  parts may have thought=True + a separate text part
    """
    try:
        parts = response["candidates"][0]["content"]["parts"]
        # Prefer a part that has text and is NOT a thought
        for part in parts:
            if part.get("thought"):
                continue
            txt = part.get("text", "")
            if txt:
                return txt
        # Fallback: first part with any text
        for part in parts:
            txt = part.get("text", "")
            if txt:
                return txt
        raise ValueError("All parts are empty or thoughts-only")
    except (KeyError, IndexError) as exc:
        raise ValueError(f"Unexpected Gemini response shape: {exc}") from exc


def _json_generation_config(max_tokens: int = 1024) -> dict:
    """Generation config for structured JSON outputs — disables thinking to save tokens."""
    return {
        "temperature": 0.1,
        "maxOutputTokens": max_tokens,
        "thinkingConfig": {"thinkingBudget": 0},
    }


def _creative_generation_config(max_tokens: int = 2048) -> dict:
    """Generation config for creative copy — thinking disabled to preserve tokens."""
    return {
        "temperature": 0.9,
        "maxOutputTokens": max_tokens,
        "thinkingConfig": {"thinkingBudget": 0},
    }


async def _call_gemini_with_retry(payload: dict, max_retries: int = 1) -> dict:
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(_gemini_url(), json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
                continue
            raise exc


# ── Fallbacks (always available) ──────────────────────────────────────────────

def _nudge_fallback(state: str, spend_pct: float, platform: str | None) -> dict:
    platform_str = platform or "this"
    return {
        "calm": {
            "title": "quick check before you shop",
            "body": f"{spend_pct:.0f}% of budget used. you're doing okay.",
            "tag": "budget check 💙",
        },
        "aware": {
            "title": "hold on a second bestie",
            "body": f"you're at {spend_pct:.0f}% — worth a pause before {platform_str}.",
            "tag": "heads up 👀",
        },
        "urgent": {
            "title": "the math is not mathing",
            "body": f"{spend_pct:.0f}% gone. {platform_str} can wait, your wallet can't.",
            "tag": "urgent 🌶️",
        },
        "crisis": {
            "title": "wallet in crisis mode fr fr",
            "body": "budget almost gone. surviving on vibes. skip this one.",
            "tag": "crisis 💀",
        },
    }.get(state, {
        "title": "quick check before you shop",
        "body": f"{spend_pct:.0f}% of budget used.",
        "tag": "budget check 💙",
    })


# ── Function 1 — Screenshot extraction ───────────────────────────────────────

async def extract_purchase_from_screenshot(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    if not GEMINI_API_KEY:
        return {"error": True, "fallback": True, "message": "Gemini API key not configured"}

    prompt = (
        "Extract order details from this content.\n"
        "Content type: screenshot\n\n"
        "Return JSON only:\n"
        "{\n"
        '  "item_name": "exact product name from receipt",\n'
        '  "platform": "Myntra|Amazon|Flipkart|Zepto|Blinkit|Swiggy|Ajio|Nykaa|Other",\n'
        '  "amount": "number only",\n'
        '  "order_date": "date shown ON THE RECEIPT in YYYY-MM-DD. THIS IS NOT TODAY\'S DATE. '
        "Read the actual date from the receipt. If no date visible: return null\",\n"
        '  "category": "food_dining_delivery|shopping_fashion|electronics_tech|'
        'entertainment_subs|health_lifestyle|others",\n'
        '  "is_consumable": "true if grocery/medicine/daily essential, false if clothing/electronics/lifestyle",\n'
        '  "subcategory": "ethnic_wear|sneakers|skincare|gadget|subscription|etc"\n'
        "}\n\n"
        "CRITICAL: order_date must come from receipt only. Never use today's date. "
        "If not visible: return null.\n"
        "Return JSON only."
    )

    image_b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}},
            ]
        }],
        "generationConfig": _json_generation_config(512),
    }

    try:
        response = await _call_gemini_with_retry(payload)
        raw_text = _get_text(response)
        data = _extract_json(raw_text)

        # Normalise amount to float
        data["amount"] = float(str(data.get("amount", 0)).replace(",", ""))
        data["is_consumable"] = bool(data.get("is_consumable", False))
        data["raw_extracted_text"] = raw_text

        order_date_str = data.get("order_date")
        if order_date_str:
            data["order_date_confidence"] = "confirmed"
        else:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            data["order_date"] = yesterday
            data["order_date_confidence"] = "estimated"

        return data
    except Exception as exc:
        logger.error("extract_purchase_from_screenshot failed: %s", exc)
        return {"error": True, "fallback": True, "message": "Could not extract purchase details"}


# ── Function 2 — Nudge copy generation ───────────────────────────────────────

async def generate_nudge_copy(
    state: str,
    spend_pct: float,
    platform: str | None,
    similar_item: str | None,
    days_since: int | None,
    category_pct: float,
) -> dict:
    fallback = _nudge_fallback(state, spend_pct, platform)

    if not GEMINI_API_KEY:
        return fallback

    prompt = (
        f"User wallet state: {state}\n"
        f"Overall budget: {spend_pct:.0f}% used\n"
        f"Platform: {platform or 'unknown'}\n"
        f"Similar item bought: {similar_item or 'none'} ({days_since or 'N/A'} days ago)\n"
        f"Category budget: {category_pct:.0f}% used\n\n"
        "Generate a SpendSense push notification for a GenZ Indian user.\n"
        "Two parts:\n"
        "1. title: punchy, max 8 words, GenZ language\n"
        "2. body: specific, mention real numbers, max 15 words\n"
        "3. tag: 2-3 word chip label + one emoji\n\n"
        "Tone rules:\n"
        "- calm state: friendly, light, encouraging\n"
        "- aware state: funny, slightly dramatic\n"
        "- urgent state: sarcastic, concerned, relatable\n"
        "- crisis state: unhinged, dramatic, but NEVER shameful\n"
        "- Always reference Indian context (zepto, myntra, blinkit, maggi, UPI)\n"
        "- Never use formal language. Never shame the user.\n"
        "- If similar_item exists: reference it specifically in the body\n\n"
        'Return JSON only — no markdown, no explanation:\n'
        '{ "title": "...", "body": "...", "tag": "..." }'
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": _creative_generation_config(512),
    }

    try:
        response = await _call_gemini_with_retry(payload)
        raw_text = _get_text(response)
        data = _extract_json(raw_text)
        # Validate required keys
        if not all(k in data for k in ("title", "body", "tag")):
            raise ValueError("Missing required keys in Gemini nudge response")
        return data
    except Exception as exc:
        logger.warning("generate_nudge_copy failed, using fallback: %s", exc)
        return fallback


# ── Function 3 — Duplicate purchase check ────────────────────────────────────

async def check_duplicate_purchase(new_item: str, recent_purchases: list) -> dict:
    _safe = {"is_duplicate": False, "matched_item": None, "days_since": None, "confidence": "unknown"}

    if not recent_purchases:
        return {**_safe, "confidence": "low"}

    if not GEMINI_API_KEY:
        return _safe

    formatted = "\n".join([
        f"- {p['item_name']} ({p['platform']}, ₹{p['amount']}, {p.get('order_date', 'unknown')})"
        for p in recent_purchases
    ])

    prompt = (
        f'Is this item semantically similar to any item in the purchase history?\n\n'
        f'Checking: "{new_item}"\n\n'
        f"Purchase history (last 60 days, non-consumables only):\n{formatted}\n\n"
        "Rules:\n"
        "- Similar means same TYPE of item (e.g. two ethnic tops, two sneakers)\n"
        "- Exact match is obviously similar\n"
        "- Different category = not similar (shoes ≠ top)\n"
        "- Consumables (groceries, medicine) are NEVER similar to anything\n"
        "- Consider colour variations (blue kurta vs floral kurta = similar)\n\n"
        'Return JSON only:\n'
        '{ "is_duplicate": true/false, "matched_item": "item name or null", '
        '"days_since": number_or_null, "confidence": "high|medium|low" }'
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": _json_generation_config(256),
    }

    try:
        response = await _call_gemini_with_retry(payload)
        raw_text = _get_text(response)
        data = _extract_json(raw_text)
        return {
            "is_duplicate": bool(data.get("is_duplicate", False)),
            "matched_item": data.get("matched_item"),
            "days_since": data.get("days_since"),
            "confidence": data.get("confidence", "medium"),
        }
    except Exception as exc:
        logger.warning("check_duplicate_purchase failed: %s", exc)
        return _safe


# ── Function 4 — Product extraction for Shop Check ───────────────────────────

async def extract_product_for_check(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    if not GEMINI_API_KEY:
        return {"error": True, "item_description": None}

    prompt = (
        "Look at this product page screenshot.\n"
        "Extract what product is being shown.\n"
        "Return JSON only:\n"
        '{ "item_description": "full description of item", '
        '"item_name": "short product name", '
        '"price": "number_or_null", '
        '"category": "clothing|electronics|food|health|entertainment|other" }'
    )

    image_b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": image_b64}},
            ]
        }],
        "generationConfig": _json_generation_config(256),
    }

    try:
        response = await _call_gemini_with_retry(payload)
        raw_text = _get_text(response)
        data = _extract_json(raw_text)
        return {
            "item_description": data.get("item_description") or data.get("item_name"),
            "item_name": data.get("item_name"),
            "price": float(data["price"]) if data.get("price") else None,
            "category": data.get("category", "other"),
        }
    except Exception as exc:
        logger.warning("extract_product_for_check failed: %s", exc)
        return {"error": True, "item_description": None}


# ── Function 5 — Morning copy generation ─────────────────────────────────────

async def generate_morning_copy(
    state: str,
    spend_pct: float,
    last_platform: str | None,
    days_since_last: int | None,
) -> dict:
    morning_fallbacks = {
        "calm": {
            "title": "good morning, financially stable human",
            "body": f"{spend_pct:.0f}% budget used. responsible adult energy.",
        },
        "aware": {
            "title": f"going to {last_platform or 'myntra'} again? bold choice.",
            "body": f"{days_since_last or 'a few'} days since last purchase. budget at {spend_pct:.0f}%.",
        },
        "urgent": {
            "title": "the math is not mathing bestie",
            "body": f"{spend_pct:.0f}% gone. we need to talk about your spending.",
        },
        "crisis": {
            "title": "okay so this month was a journey",
            "body": f"{spend_pct:.0f}% budget gone. surviving on maggi and hope.",
        },
    }
    fallback = morning_fallbacks.get(state, morning_fallbacks["calm"])

    if not GEMINI_API_KEY:
        return fallback

    prompt = (
        f"Generate a morning push notification for a SpendSense user.\n\n"
        f"State: {state} | Budget used: {spend_pct:.0f}%\n"
        f"Last purchase: {last_platform or 'unknown'} ({days_since_last or 'unknown'} days ago)\n\n"
        "Sample tone per state (generate FRESH copy, don't copy these):\n"
        'calm:   title "good morning, financially stable human" / body "56% used. responsible adult energy."\n'
        'aware:  title "going to myntra again? bold choice." / body "12 days since last fashion purchase."\n'
        'urgent: title "the math is not mathing bestie" / body "₹X gone. Y days left. we need to talk."\n'
        'crisis: title "okay so this month was a journey" / body "91% gone. surviving on maggi and hope."\n\n'
        "Rules: GenZ tone, Indian context, never shame, use real numbers.\n"
        'Return JSON only: { "title": "...", "body": "..." }'
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": _creative_generation_config(256),
    }

    try:
        response = await _call_gemini_with_retry(payload)
        raw_text = _get_text(response)
        data = _extract_json(raw_text)
        if not all(k in data for k in ("title", "body")):
            raise ValueError("Missing keys")
        return data
    except Exception as exc:
        logger.warning("generate_morning_copy failed, using fallback: %s", exc)
        return fallback
