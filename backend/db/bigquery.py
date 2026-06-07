import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
_bq_client = None


def get_bigquery_client():
    return _bq_client


def init_bigquery() -> None:
    global _bq_client

    project_id = os.getenv("GCP_PROJECT_ID", "")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    if not project_id or "placeholder" in project_id.lower():
        logger.warning(
            "BigQuery not connected — wallet state will use cached values"
        )
        return

    if credentials_path and not _credentials_file_exists(credentials_path):
        logger.warning(
            "BigQuery not connected — credentials file not found: %s",
            credentials_path,
        )
        return

    try:
        from google.cloud import bigquery  # noqa: PLC0415

        _bq_client = bigquery.Client(project=project_id)
        logger.info("BigQuery connected: project=%s", project_id)
    except Exception as exc:
        logger.warning(
            "BigQuery not connected — wallet state will use cached values: %s",
            exc,
        )
        _bq_client = None


def _credentials_file_exists(path: str) -> bool:
    if not path:
        return False
    try:
        import pathlib  # noqa: PLC0415

        return pathlib.Path(path).exists()
    except Exception:
        return False
