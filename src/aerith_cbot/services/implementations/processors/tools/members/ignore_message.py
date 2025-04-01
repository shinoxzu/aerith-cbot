import logging

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import ChatState

from . import ToolCommand


class IgnoreMessageToolCommand(ToolCommand):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, chat_id: int) -> str:
        chat_state = await self._db_session.get_one(ChatState, chat_id)

        chat_state.listening_streak = 0

        if chat_state.ignoring_streak >= 10:
            self._logger.info("Ignoring streak in chat %s reached limit; unfocusing", chat_id)

            chat_state.ignoring_streak = 0
            chat_state.is_focused = False
        else:
            chat_state.ignoring_streak += 1

            self._logger.info(
                "Ignoring streak in chat %s is %s now",
                chat_id,
                chat_state.ignoring_streak,
            )

        await self._db_session.commit()

        return """
        Сообщение проигнорировано.
        Будь внимательна: точно ли говорят не с тобой? Если обращаются к тебе, ответь.
        """
