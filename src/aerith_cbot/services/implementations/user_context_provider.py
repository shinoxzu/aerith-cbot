import logging
import time

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio.session import AsyncSession

from aerith_cbot.database.models import UserGroupLastContact, UserPersonalContext
from aerith_cbot.services.abstractions import UserContextProvider


class DefaultUserContextProvider(UserContextProvider):
    LAST_CONTACT_TIME = 900

    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def provide_context(self, chat_id: int) -> str:
        user_ids = await self._get_last_contact_users(chat_id)

        stmt = select(UserPersonalContext).where(UserPersonalContext.user_id._in(user_ids))
        result = await self._db_session.execute(stmt)
        personal_context_list = [row[0] for row in result.all()]
        result_context = self._format_context(personal_context_list)
        return result_context

    async def update_context(self, user_id: int, context: str) -> None:
        await self._db_session.execute(
            update(UserPersonalContext)
            .where(UserPersonalContext.user_id == user_id)
            .values(context=context)
        )

    async def _get_last_contact_users(self, chat_id: int) -> list[int]:
        stmt = (
            select(UserGroupLastContact.user_id)
            .where(
                UserGroupLastContact.chat_id == chat_id,
                UserGroupLastContact.last_contacted_time > time.time() - self.LAST_CONTACT_TIME,
            )
            .limit(5)
        )
        user_ids_result = await self._db_session.execute(stmt)
        user_ids = [row[0] for row in user_ids_result.all()]

        return user_ids

    def _format_context(self, personal_context_list: list[UserPersonalContext]) -> str:
        return "\n\n".join(
            [
                f"user_id={user_context.user_id}: {user_context.context}"
                for user_context in personal_context_list
            ]
        )
