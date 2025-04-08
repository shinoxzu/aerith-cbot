import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.database.models import UserSupport as UserSupportDbModel
from aerith_cbot.services.abstractions import SupportService
from aerith_cbot.services.abstractions.models import UserSupport


class DefaultSupportService(SupportService):
    def __init__(self, db_session: AsyncSession) -> None:
        super().__init__()

        self._db_session = db_session
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
                user_id=user_id, end_timestamp=int(time.time()) + interval
            )
            self._db_session.add(user_supporter)
        else:
            current_time = int(time.time())
            if user_supporter.end_timestamp < current_time:
                user_supporter.end_timestamp = current_time

            user_supporter.end_timestamp = int(time.time()) + interval

        await self._db_session.commit()
