import logging

from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState

from .base import ToolCommand


class WaitForUserEndToolCommand(ToolCommand):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, message: Message) -> str:
        chat_state = await self._db_session.get_one(ChatState, message.chat.id)

        chat_state.listening_streak += 1

        self._logger.info(
            "Listening streak in chat %s is %s now",
            message.chat.id,
            chat_state.listening_streak,
        )

        await self._db_session.commit()

        return "ожидаю"
