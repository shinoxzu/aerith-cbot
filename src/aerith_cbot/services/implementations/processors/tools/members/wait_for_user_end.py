import logging

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState

from . import ToolCommand


class WaitForUserEndToolCommand(ToolCommand):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

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
            return "Ты слишком долго слушаешь пользователя. Пора ответить ему!"
        return """
        Пользователь не завершил мысль, игнорируем.
        Будь внимательна: точно ли он не завершил мысль? Если он ждет твоего ответа, ответь ему.
        """
