import logging

logger = logging.getLogger(__name__)

try:
    from google.adk.agents import Agent
    from .tools import (
        get_wallet_state,
        fire_nudge,
        get_purchase_history,
        sync_transactions,
        get_monthly_report,
    )
    from .prompts import SYSTEM_PROMPT

    spendsense_agent = Agent(
        name="spendsense_agent",
        model="gemini-2.5-flash",
        description="Behavioral finance agent that stops impulse spending",
        instruction=SYSTEM_PROMPT,
        tools=[
            get_wallet_state,
            fire_nudge,
            get_purchase_history,
            sync_transactions,
            get_monthly_report,
        ],
    )
    ADK_AVAILABLE = True
    logger.info("SpendSense ADK agent initialised successfully")

except ImportError as e:
    logger.warning("google-adk not available (%s) — agent layer disabled", e)
    spendsense_agent = None
    ADK_AVAILABLE = False
