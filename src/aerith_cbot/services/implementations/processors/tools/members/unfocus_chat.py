from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LLMConfig
from aerith_cbot.database.models import ChatState

from . import ToolCommand


class UnfocusChatToolCommand(ToolCommand):
    def __init__(self, db_session: AsyncSession, llm_config: LLMConfig) -> None:
        super().__init__()

        self._db_session = db_session
        self._llm_config = llm_config

    async def execute(self, arguments: str, chat_id: int) -> str:
        chat_state = await self._db_session.get_one(ChatState, chat_id)
        chat_state.is_focused = False
        await self._db_session.commit()

        return self._llm_config.additional_instructions.chat_unfocused_by_request
