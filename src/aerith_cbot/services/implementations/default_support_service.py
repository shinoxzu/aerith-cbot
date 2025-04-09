import asyncio
import logging
import time

from aiogram import Bot
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import UserSupport as UserSupportDbModel
from aerith_cbot.services.abstractions import SupportService
from aerith_cbot.services.abstractions.models import UserSupport


class DefaultSupportService(SupportService):
    PROLONG_NOTIFY_MIN_TIME = 86_400
    PROLONG_MSG_INTERVAL = 0.3

    def __init__(self, db_session: AsyncSession, bot: Bot) -> None:
        super().__init__()

        self._db_session = db_session
        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def is_active_supporter(self, user_id: int) -> bool:
        user_supporter = await self._db_session.get(UserSupportDbModel, user_id)
        return user_supporter is not None and user_supporter.end_timestamp > int(time.time())

    async def fetch_supporter(self, user_id: int) -> UserSupport | None:
        raw_user_supporter = await self._db_session.get(UserSupportDbModel, user_id)

        if raw_user_supporter is None:
            return None

        return UserSupport(user_id=user_id, end_timestamp=raw_user_supporter.end_timestamp)

    async def prolong_support(self, user_id: int, interval: int) -> None:
        self._logger.info("Prolonging support for user %s for %s seconds", user_id, interval)

        user_supporter = await self._db_session.get(
            UserSupportDbModel, user_id, with_for_update=True
        )

        if user_supporter is None:
            user_supporter = UserSupportDbModel(
                user_id=user_id, end_timestamp=int(time.time()) + interval, is_notified=True
            )
            self._db_session.add(user_supporter)
        else:
            current_time = int(time.time())
            if user_supporter.end_timestamp < current_time:
                user_supporter.end_timestamp = current_time

            user_supporter.end_timestamp = int(time.time()) + interval

        await self._db_session.commit()

    async def notify_users_to_prolong(self) -> None:
        current_time = int(time.time())
        stmt = select(UserSupportDbModel).where(
            UserSupportDbModel.end_timestamp - current_time
            < DefaultSupportService.PROLONG_NOTIFY_MIN_TIME,
            UserSupportDbModel.is_notified == False,  # noqa
        )
        result = await self._db_session.execute(stmt)
        support_users = result.scalars()

        for support_user in support_users:
            try:
                await self._bot.send_message(
                    chat_id=support_user.user_id,
                    text="привет! твоя поддержка заканчивается меньше, чем через сутки...",
                )
            except Exception as err:
                self._logger.error(
                    "Cannot send message to %s cause of %s", support_user.user_id, err, exc_info=err
                )
            finally:
                await asyncio.sleep(DefaultSupportService.PROLONG_MSG_INTERVAL)

        support_user_ids = [support_user.user_id for support_user in support_users]
        regular_stmt = (
            update(UserSupportDbModel)
            .where(UserSupportDbModel.user_id.in_(support_user_ids))
            .values(
                is_notified=True,
            )
        )
        await self._db_session.execute(regular_stmt)
        await self._db_session.commit()
