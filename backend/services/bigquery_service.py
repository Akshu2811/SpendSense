import logging
import os
from datetime import date

logger = logging.getLogger(__name__)

DATASET = os.getenv("BIGQUERY_DATASET", "spendsense_data")

EMPTY_CATEGORIES: dict = {
    "food_dining_delivery": 0.0,
    "shopping_fashion": 0.0,
    "electronics_tech": 0.0,
    "entertainment_subs": 0.0,
    "health_lifestyle": 0.0,
    "others": 0.0,
}


async def get_monthly_total(project_id: str, month_start: date) -> float:
    from db.bigquery import get_bigquery_client  # noqa: PLC0415

    client = get_bigquery_client()
    if client is None:
        return 0.0

    query = f"""
        SELECT SUM(amount) AS total
        FROM `{project_id}.{DATASET}.google_sheets.transactions`
        WHERE DATE(date) >= '{month_start}'
        AND is_debit = true
    """
    try:
        result = client.query(query).result()
        for row in result:
            return float(row.total or 0.0)
        return 0.0
    except Exception as exc:
        logger.error("BigQuery get_monthly_total failed: %s", exc)
        return 0.0


async def get_category_breakdown(project_id: str, month_start: date) -> dict:
    from db.bigquery import get_bigquery_client  # noqa: PLC0415

    client = get_bigquery_client()
    if client is None:
        return dict(EMPTY_CATEGORIES)

    query = f"""
        SELECT category, SUM(amount) AS total
        FROM `{project_id}.{DATASET}.google_sheets.transactions`
        WHERE DATE(date) >= '{month_start}'
        AND is_debit = true
        GROUP BY category
    """
    try:
        result = client.query(query).result()
        breakdown = dict(EMPTY_CATEGORIES)
        for row in result:
            if row.category in breakdown:
                breakdown[row.category] = float(row.total or 0.0)
        return breakdown
    except Exception as exc:
        logger.error("BigQuery get_category_breakdown failed: %s", exc)
        return dict(EMPTY_CATEGORIES)


async def get_transaction_frequency(project_id: str, days: int = 7) -> list:
    from db.bigquery import get_bigquery_client  # noqa: PLC0415

    client = get_bigquery_client()
    if client is None:
        return []

    query = f"""
        SELECT merchant, COUNT(*) AS frequency
        FROM `{project_id}.{DATASET}.google_sheets.transactions`
        WHERE DATE(date) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        AND is_debit = true
        GROUP BY merchant
        ORDER BY frequency DESC
        LIMIT 10
    """
    try:
        result = client.query(query).result()
        return [
            {"merchant": row.merchant, "frequency": int(row.frequency)}
            for row in result
        ]
    except Exception as exc:
        logger.error("BigQuery get_transaction_frequency failed: %s", exc)
        return []
