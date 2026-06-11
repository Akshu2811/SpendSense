from google import genai
from google.genai import types
import os, asyncio, json, re, logging
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GCP_PROJECT_ID", "spendsense-498709"),
        location="global"
    )
    model_name = "gemini-3.1-flash-lite"
    logger.info("Gemini 3.1 Flash Lite initialised via google-genai")
except Exception as e:
    client = None
    model_name = None
    logger.warning(f"Gemini init failed — fallback mode active: {e}")


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


def _json_config(max_tokens: int = 1024) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(temperature=0.1, max_output_tokens=max_tokens)


def _creative_config(max_tokens: int = 2048) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(temperature=0.9, max_output_tokens=max_tokens)


async def _call_with_retry(contents, config, max_retries: int = 1) -> str:
    """Run synchronous google-genai call in executor; sleep 2s and retry once on quota error."""
    def _sync():
        return client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

    loop = asyncio.get_running_loop()
    for attempt in range(max_retries + 1):
        try:
            response = await loop.run_in_executor(None, _sync)
            return response.text
        except Exception as exc:
            is_quota = "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc).upper()
            if attempt < max_retries and is_quota:
                await asyncio.sleep(2)
                continue
            raise


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
    if client is None:
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

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    try:
        raw_text = await _call_with_retry([image_part, prompt], _json_config(512))
        data = _extract_json(raw_text)
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            raise ValueError("Unexpected response format")

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


# ── Function 1b — Multi-screenshot extraction ────────────────────────────────

async def extract_from_multiple_screenshots(
    images: list[bytes],
    mime_types: list[str],
) -> dict:
    if client is None:
        return {"error": True, "fallback": True, "message": "Gemini API key not configured"}

    parts = []
    for img_bytes, mime in zip(images, mime_types):
        parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))

    n = len(images)
    parts.append(
        f"These {n} screenshot{'s are' if n > 1 else ' is'} from the same order confirmation.\n"
        "They may show different parts — items on one, date/total on another.\n\n"
        "Extract the complete order details by combining all screenshots.\n"
        "Return JSON only:\n"
        "{\n"
        '  "item_name": "exact product name",\n'
        '  "platform": "Myntra|Amazon|Flipkart|Zepto|Blinkit|Swiggy|Ajio|Nykaa|Other",\n'
        '  "amount": "number only (total order amount)",\n'
        '  "order_date": "date shown ON THE RECEIPT in YYYY-MM-DD. '
        "Read from whichever screenshot shows it. If not visible in any: return null\",\n"
        '  "category": "food_dining_delivery|shopping_fashion|electronics_tech|'
        'entertainment_subs|health_lifestyle|others",\n'
        '  "is_consumable": "true if grocery/medicine/daily essential, false otherwise",\n'
        '  "subcategory": "ethnic_wear|sneakers|skincare|gadget|subscription|etc",\n'
        '  "items_found": ["list", "of", "all", "item", "names", "if", "multiple"]\n'
        "}\n\n"
        "CRITICAL: Combine information across all screenshots. "
        "order_date must come from receipt only. Never use today's date. "
        "Return JSON only."
    )

    try:
        raw_text = await _call_with_retry(parts, _json_config(512))
        parsed = _extract_json(raw_text)
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}
        if not isinstance(parsed, dict):
            raise ValueError("Unexpected response format")

        parsed["amount"] = float(str(parsed.get("amount", 0)).replace(",", ""))
        parsed["is_consumable"] = bool(parsed.get("is_consumable", False))
        parsed["raw_extracted_text"] = raw_text

        if parsed.get("order_date"):
            parsed["order_date_confidence"] = "confirmed"
        else:
            yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            parsed["order_date"] = yesterday
            parsed["order_date_confidence"] = "estimated"

        return parsed
    except Exception as exc:
        logger.error("extract_from_multiple_screenshots failed: %s", exc)
        return {"error": True, "fallback": True, "message": "Could not extract purchase details"}


# ── Function 2 — Nudge copy generation ───────────────────────────────────────

async def generate_nudge_copy(
    state: str,
    spend_pct: float,
    platform: str | None,
    similar_item: str | None,
    days_since: int | None,
    category_pct: float | None,
) -> dict:
    fallback = _nudge_fallback(state, spend_pct, platform)

    if client is None:
        return fallback

    if category_pct is not None:
        budget_line = f"Category budget used: {category_pct:.0f}% — reference this percentage in the copy\n"
    else:
        budget_line = (
            f"Overall budget used: {spend_pct:.0f}% — reference this percentage in the copy. "
            "Do NOT mention any specific category percentage.\n"
        )

    prompt = (
        f"User wallet state: {state}\n"
        f"Overall budget: {spend_pct:.0f}% used\n"
        f"Platform the user is about to open: {platform or 'unknown'}\n"
        f"Similar item bought: {similar_item or 'none'} ({days_since or 'N/A'} days ago)\n"
        + budget_line + "\n"
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
        f"- Only reference {platform or 'this app'} by name — never mention other shopping apps unless the user has purchase history there\n"
        "- You may reference Indian GenZ culture (maggi, UPI, 'not it', 'the math') but name only the platform above as the shopping destination\n"
        "- Never use formal language. Never shame the user.\n"
        "- If similar_item exists: reference it specifically in the body\n\n"
        'Return JSON only — no markdown, no explanation:\n'
        '{ "title": "...", "body": "...", "tag": "..." }'
    )

    try:
        raw_text = await _call_with_retry(prompt, _creative_config(512))
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

    if client is None:
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

    try:
        raw_text = await _call_with_retry(prompt, _json_config(256))
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
    if client is None:
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

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    try:
        raw_text = await _call_with_retry([image_part, prompt], _json_config(256))
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

    if client is None:
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

    try:
        raw_text = await _call_with_retry(prompt, _creative_config(256))
        data = _extract_json(raw_text)
        if not all(k in data for k in ("title", "body")):
            raise ValueError("Missing keys")
        return data
    except Exception as exc:
        logger.warning("generate_morning_copy failed, using fallback: %s", exc)
        return fallback
