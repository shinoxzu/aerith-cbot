import logging

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LLMConfig
from aerith_cbot.database.models import ChatState

from . import ToolCommand


class WaitForUserEndToolCommand(ToolCommand):
    def __init__(self, db_session: AsyncSession, llm_config: LLMConfig) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)
        self._llm_config = llm_config

    async def execute(self, arguments: str, chat_id: int) -> str:
        chat_state = await self._db_session.get_one(ChatState, chat_id)

        chat_state.ignoring_streak = 0
        chat_state.listening_streak += 1

        self._logger.info(
            "Listening streak in chat %s is %s now",
            chat_id,
            chat_state.listening_streak,
        )

        await self._db_session.commit()

        if chat_state.listening_streak >= 5:
            return self._llm_config.additional_instructions.too_long_listening
        return self._llm_config.additional_instructions.user_not_completed_thought
