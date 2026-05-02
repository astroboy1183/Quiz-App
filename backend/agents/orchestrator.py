import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Master router for a quiz session.
    Sprint 1: stubs only — logs session lifecycle events.
    Full LangGraph state machine wired in Sprint 3+.
    """

    async def on_session_start(
        self, session_id: uuid.UUID, topic: str, difficulty: str
    ) -> None:
        logger.info(
            "[Orchestrator] Session started | id=%s topic=%s difficulty=%s",
            session_id,
            topic,
            difficulty,
        )

    async def on_answer_submitted(
        self, session_id: uuid.UUID, question_number: int, is_correct: bool
    ) -> None:
        logger.info(
            "[Orchestrator] Answer submitted | session=%s q=%d correct=%s",
            session_id,
            question_number,
            is_correct,
        )

    async def on_session_end(
        self, session_id: uuid.UUID, score: int, accuracy: float
    ) -> None:
        logger.info(
            "[Orchestrator] Session ended | id=%s score=%d accuracy=%.1f%%",
            session_id,
            score,
            accuracy * 100,
        )

    async def route(self, event: str, payload: dict[str, Any]) -> None:
        """Generic routing hook — will dispatch to sub-agents in later sprints."""
        logger.info(
            "[Orchestrator] Event: %s | payload keys: %s",
            event,
            list(payload.keys()),
        )


orchestrator = OrchestratorAgent()
