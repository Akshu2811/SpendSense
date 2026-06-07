import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.join(_here, "..")
# Try backend/.env first, then root .env
load_dotenv(os.path.join(_root, "backend", ".env"))
load_dotenv(os.path.join(_root, ".env"))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

APP_NAME = "spendsense"

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part
    from spendsense_agent.agent import spendsense_agent, ADK_AVAILABLE
    from spendsense_agent.prompts import MORNING_ANALYSIS_PROMPT, PRE_SHOP_PROMPT

    if not ADK_AVAILABLE or spendsense_agent is None:
        raise ImportError("ADK agent not initialised")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=spendsense_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    async def run_morning_check(user_id: str, user_token: str) -> str:
        """Run the morning spending check for a user."""
        import uuid
        session_id = f"morning_{user_id}_{uuid.uuid4().hex[:8]}"
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        message = Content(
            role="user",
            parts=[Part(text=f"Run morning check. User token: {user_token}. {MORNING_ANALYSIS_PROMPT}")],
        )
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    text = event.content.parts[0].text or "Morning check completed"
                    logger.info("Morning check complete for user %s", user_id)
                    return text
        return "Morning check completed"

    async def run_pre_shop_check(user_id: str, user_token: str, platform: str) -> str:
        """Run a pre-shop check when user is about to open a shopping app."""
        import uuid
        session_id = f"preshop_{user_id}_{platform}_{uuid.uuid4().hex[:8]}"
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        prompt = PRE_SHOP_PROMPT.format(platform=platform)
        message = Content(
            role="user",
            parts=[Part(text=f"User token: {user_token}. {prompt}")],
        )
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    return event.content.parts[0].text or "Pre-shop check completed"
        return "Pre-shop check completed"

    _ADK_RUNNER_READY = True
    logger.info("ADK runner ready")

except ImportError as e:
    logger.warning("ADK runner unavailable (%s) — fallback mode active", e)
    _ADK_RUNNER_READY = False

    async def run_morning_check(user_id: str, user_token: str) -> str:
        logger.warning("ADK unavailable — skipping morning check for %s", user_id)
        return "ADK unavailable — morning check skipped"

    async def run_pre_shop_check(user_id: str, user_token: str, platform: str) -> str:
        logger.warning("ADK unavailable — skipping pre-shop check for %s", user_id)
        return "ADK unavailable — pre-shop check skipped"


if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else "test_token"
    asyncio.run(run_morning_check("test_user", token))
