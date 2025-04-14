import logging

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import (
    ChatState,
    GroupLimitEntry,
    Message,
    UserGroupLastContact,
)
from aerith_cbot.services.abstractions import ChatMigrationService


class DefaultChatMigrationService(ChatMigrationService):
    MODELS_TO_UPDATE = [
        ChatState,
        GroupLimitEntry,
        Message,
        UserGroupLastContact,
    ]

    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def update(self, old_chat_id: int, chat_id: int) -> None:
        for model in self.MODELS_TO_UPDATE:
            stmt = update(model).where(model.chat_id == old_chat_id).values(chat_id=chat_id)
            await self._db_session.execute(stmt)

        await self._db_session.commit()
        self._logger.info(
            "Successfully migrate from chat_id=%s to chat_id=%s", old_chat_id, chat_id
        )
