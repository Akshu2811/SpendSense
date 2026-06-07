async def extract_purchase_from_screenshot(image_bytes: bytes) -> dict:
    return {"stub": True, "message": "Gemini Vision — implemented in Session 2"}


async def generate_nudge_copy(
    state: str,
    spend_pct: float,
    platform: str | None,
    similar_item: str | None,
    days_since: int | None,
    category_pct: float,
) -> dict:
    fallbacks = {
        "calm": {
            "title": "quick check before you shop",
            "body": f"{spend_pct:.0f}% of budget used.",
            "tag": "budget check 💙",
        },
        "aware": {
            "title": "hold on a second",
            "body": f"You're at {spend_pct:.0f}% — worth a pause.",
            "tag": "heads up 👀",
        },
        "urgent": {
            "title": "budget getting tight",
            "body": f"{spend_pct:.0f}% gone. {platform or 'this'} can wait.",
            "tag": "urgent 🌶️",
        },
        "crisis": {
            "title": "wallet in crisis mode",
            "body": "Budget almost gone. Skip this one.",
            "tag": "crisis 💀",
        },
    }
    return fallbacks.get(state, fallbacks["aware"])


async def check_duplicate_purchase(new_item: str, recent_purchases: list) -> dict:
    return {"is_duplicate": False, "matched_item": None, "confidence": "unknown"}
