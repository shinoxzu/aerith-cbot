import logging
import time

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from aerith_cbot.database.models import UserGroupLastContact, UserPersonalContext
from aerith_cbot.services.abstractions import UserContextProvider


class DefaultUserContextProvider(UserContextProvider):
    LAST_CONTACT_TIME = 900

    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
        self._logger = logging.getLogger(__name__)

    async def provide_private_user_context(self, user_id: int) -> str | None:
        stmt = select(UserPersonalContext).where(UserPersonalContext.user_id == user_id)
        result = await self._db_session.scalar(stmt)

        if result is not None:
            return self._format_private_user_context(result)
        else:
            return None

    async def provide_chat_users_context(self, chat_id: int) -> str | None:
        user_ids = await self._get_last_contact_users(chat_id)

        stmt = select(UserPersonalContext).where(UserPersonalContext.user_id.in_(user_ids))
        result = await self._db_session.scalars(stmt)
        personal_context_list = list(result)

        if personal_context_list:
            return self._format_chat_users_context(personal_context_list)
        else:
            return None

    async def update_context(self, user_id: int, context: str) -> None:
        last_contact = UserPersonalContext(user_id=user_id, context=context)
        await self._db_session.merge(last_contact)
        await self._db_session.commit()

    async def _get_last_contact_users(self, chat_id: int) -> list[int]:
        stmt = (
            select(UserGroupLastContact.user_id)
            .where(
                UserGroupLastContact.chat_id == chat_id,
                UserGroupLastContact.last_contacted_time > time.time() - self.LAST_CONTACT_TIME,
            )
            .order_by(desc(UserGroupLastContact.last_contacted_time))
            .limit(5)
        )
        result = await self._db_session.scalars(stmt)
        user_ids = list(result)

        return user_ids

    def _format_chat_users_context(self, personal_context_list: list[UserPersonalContext]) -> str:
        return (
            'Контексты пользователей:"""\n'
            + (
                "\n".join(
                    [
                        f"user_id={user_context.user_id}: {user_context.context}"
                        for user_context in personal_context_list
                    ]
                )
            )
            + '"""'
        )

    def _format_private_user_context(self, personal_context: UserPersonalContext) -> str:
        return f'Контекст пользователя:"""\n{personal_context.context}"""'
