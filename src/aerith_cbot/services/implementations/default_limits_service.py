import logging
import time

from sqlalchemy import desc, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LimitsConfig
from aerith_cbot.database.models import (
    GroupLimitEntry,
    UserGroupLastContact,
    UserGroupLimitEntry,
    UserPrivateLimitEntry,
    UserSupport,
)
from aerith_cbot.services.abstractions import LimitsService
from aerith_cbot.services.abstractions.support_service import SupportService


class DefaultLimitsService(LimitsService):
    RECENTLY_ACTIVE_USERS_INTERVAL = 180  # 3 minutes
    TOTAL_ACTIVE_USERS_INTERVAL = 259_200  # 3 days

    def __init__(
        self, db_session: AsyncSession, limits_config: LimitsConfig, support_service: SupportService
    ) -> None:
        self._db_session = db_session
        self._logger = logging.getLogger(__name__)
        self._limits_config = limits_config
        self._support_service = support_service

    async def check_private_limit(self, user_id: int) -> bool:
        limit_entry = await self._create_or_fetch_user_limit_entry(user_id)

        current_time = int(time.time())

        if current_time - limit_entry.last_ref_time > self._limits_config.private_cooldown:
            limit_entry.last_ref_time = current_time

            if await self._support_service.is_active_supporter(user_id):
                limit_entry.remain_tokens = self._limits_config.private_support_tokens_limit
            else:
                limit_entry.remain_tokens = self._limits_config.private_tokens_limit

            await self._db_session.commit()

            self._logger.debug("limit for user %s refreshed", user_id)

        return limit_entry.remain_tokens > 0

    async def subtract_private_tokens(self, user_id: int, tokens_count: int) -> None:
        self._logger.debug("subtracting %s tokens from user %s", tokens_count, user_id)

        limit_entry = await self._create_or_fetch_user_limit_entry(user_id)
        await self._db_session.execute(
            update(UserPrivateLimitEntry)
            .where(UserPrivateLimitEntry.user_id == limit_entry.user_id)
            .values(remain_tokens=UserPrivateLimitEntry.remain_tokens - tokens_count)
        )
        await self._db_session.commit()

    async def _create_or_fetch_user_limit_entry(self, user_id) -> UserPrivateLimitEntry:
        limit_entry = await self._db_session.get(UserPrivateLimitEntry, user_id)
        if limit_entry is None:
            self._logger.debug("Adding new limit_entry for user: %s", user_id)

            limit_entry = UserPrivateLimitEntry(
                user_id=user_id,
                last_ref_time=int(time.time()),
                remain_tokens=self._limits_config.private_tokens_limit,
            )
            self._db_session.add(limit_entry)
            await self._db_session.commit()

        return limit_entry

    async def check_group_limit(self, user_id: int, chat_id: int) -> bool:
        # create (if non-exists) user global limit info and update (or create)
        # local last contacted time with Aerith
        await self._update_user_contact_and_ensure_limit_entry(user_id, chat_id)

        # TODO: optimiation. call this only if some second passed
        await self._update_group_members_limits(
            chat_id, int(time.time()) - DefaultLimitsService.TOTAL_ACTIVE_USERS_INTERVAL
        )

        group_limit_entry = await self._create_or_fetch_group_limit_entry(chat_id)

        current_time = int(time.time())

        # reset group limit if needed
        if current_time - group_limit_entry.last_ref_time > self._limits_config.group_cooldown:
            group_limit_entry.last_ref_time = current_time
            group_limit_entry.remain_tokens = self._limits_config.group_generic_tokens_limit
            await self._db_session.commit()

            self._logger.debug("Limit in %s refreshed", chat_id)

        # if group limit is all used
        if group_limit_entry.remain_tokens <= 0:
            self._logger.info("Limit in group %s cause group tokens spended", chat_id)
            return False

        # fetch recently active users with most tokens available
        # if there is no such a user (it's unpossible actually)
        top_recent_user_limit_entry = await self._fetch_top_user_limit_entry(
            chat_id, int(time.time()) - DefaultLimitsService.RECENTLY_ACTIVE_USERS_INTERVAL
        )
        if top_recent_user_limit_entry is None:
            self._logger.warn("Cannot find any recent user in chat %s", chat_id)
            return False

        # if there is no tokens in recently contacted users
        if top_recent_user_limit_entry.remain_tokens <= 0:
            # we trying to fetch limits of almost all users in the chat
            # if there is no such a user (it's also unpossible)
            top_tokens_user_limit_entry = await self._fetch_top_user_limit_entry(
                chat_id, int(time.time()) - DefaultLimitsService.TOTAL_ACTIVE_USERS_INTERVAL
            )
            if top_tokens_user_limit_entry is None:
                self._logger.warn("Cannot find any user in chat %s", chat_id)
                return False

            # we cant spend all of tokens for non-recently active user,
            # so we count limit for spending
            # for example, if coeff for max using is 0.8 and all available
            # tokens is 100, min_tokens will be eq to 20
            min_tokens = (
                1 - self._limits_config.group_per_user_max_other_usage_coeff
            ) * self._limits_config.group_per_user_tokens_limit

            # if we spend maximum of available tokens (if remain < 20)
            if top_tokens_user_limit_entry.remain_tokens <= min_tokens:
                self._logger.info("Limit in group %s cause all users tokens spended", chat_id)
                return False

        return True

    async def subtract_group_tokens(self, chat_id: int, tokens_count: int) -> None:
        self._logger.debug("subtracting %s tokens from group %s", tokens_count, chat_id)

        top_recent_user_limit_entry = await self._fetch_top_user_limit_entry(
            chat_id, int(time.time()) - DefaultLimitsService.RECENTLY_ACTIVE_USERS_INTERVAL
        )
        top_total_user_limit_entry = await self._fetch_top_user_limit_entry(
            chat_id, int(time.time()) - DefaultLimitsService.TOTAL_ACTIVE_USERS_INTERVAL
        )

        if (
            top_recent_user_limit_entry is not None
            and top_recent_user_limit_entry.remain_tokens > 0
        ):
            user_id_to_subtract = top_recent_user_limit_entry.user_id
            self._logger.info(
                "user %s was selected for subtraction in group %s (recent): %s",
                user_id_to_subtract,
                chat_id,
                top_recent_user_limit_entry,
            )
        elif top_total_user_limit_entry is not None:
            user_id_to_subtract = top_total_user_limit_entry.user_id
            self._logger.info(
                "user %s was selected for subtraction in group %s (non-recent): %s",
                user_id_to_subtract,
                chat_id,
                top_total_user_limit_entry,
            )
        else:
            return

        await self._db_session.execute(
            update(UserGroupLimitEntry)
            .where(UserGroupLimitEntry.user_id == user_id_to_subtract)
            .values(remain_tokens=UserGroupLimitEntry.remain_tokens - tokens_count)
        )
        await self._db_session.execute(
            update(GroupLimitEntry)
            .where(GroupLimitEntry.chat_id == chat_id)
            .values(remain_tokens=GroupLimitEntry.remain_tokens - tokens_count)
        )
        await self._db_session.commit()

    async def _create_or_fetch_group_limit_entry(self, chat_id: int) -> GroupLimitEntry:
        limit_entry = await self._db_session.get(GroupLimitEntry, chat_id)
        if limit_entry is None:
            self._logger.info("Adding new group_limit_entry for chat: %s", chat_id)

            limit_entry = GroupLimitEntry(
                chat_id=chat_id,
                last_ref_time=int(time.time()),
                remain_tokens=self._limits_config.group_generic_tokens_limit,
            )
            self._db_session.add(limit_entry)
            await self._db_session.commit()

        return limit_entry

    async def _fetch_top_user_limit_entry(
        self,
        chat_id: int,
        min_last_contacted_time: int,
    ) -> UserGroupLimitEntry | None:
        stmt = (
            select(UserGroupLimitEntry)
            .join(
                UserGroupLastContact,
                (UserGroupLastContact.user_id == UserGroupLimitEntry.user_id)
                & (UserGroupLastContact.chat_id == chat_id),
            )
            .where(
                UserGroupLastContact.last_contacted_time >= min_last_contacted_time,
            )
            .order_by(
                desc(UserGroupLimitEntry.remain_tokens),
                desc(UserGroupLastContact.last_contacted_time),
            )
            .limit(1)
        )
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def _update_user_contact_and_ensure_limit_entry(self, user_id: int, chat_id: int) -> None:
        current_time = int(time.time())

        last_contact = UserGroupLastContact(
            chat_id=chat_id, user_id=user_id, last_contacted_time=current_time
        )
        await self._db_session.merge(last_contact)

        stmt = insert(UserGroupLimitEntry).values(
            user_id=user_id,
            last_ref_time=current_time,
            remain_tokens=self._limits_config.group_per_user_tokens_limit,
        )
        stmt = stmt.on_conflict_do_nothing(index_elements=["user_id"])

        await self._db_session.execute(stmt)
        await self._db_session.commit()

    async def _update_group_members_limits(
        self, chat_id: int, min_last_contacted_time: int
    ) -> None:
        stmt = select(UserGroupLastContact.user_id).where(
            UserGroupLastContact.chat_id == chat_id,
            UserGroupLastContact.last_contacted_time >= min_last_contacted_time,
        )
        result = await self._db_session.execute(stmt)
        last_contacted_user_ids = [row[0] for row in result.all()]

        current_time = int(time.time())

        supporter_stmt = select(UserSupport.user_id).where(
            UserSupport.user_id.in_(last_contacted_user_ids),
            UserSupport.end_timestamp > current_time,
        )
        supporter_result = await self._db_session.execute(supporter_stmt)

        supporter_user_ids = set([row[0] for row in supporter_result.all()])
        regular_user_ids = list(set(last_contacted_user_ids) - supporter_user_ids)

        if regular_user_ids:
            regular_stmt = (
                update(UserGroupLimitEntry)
                .where(
                    UserGroupLimitEntry.user_id.in_(regular_user_ids),
                    current_time - UserGroupLimitEntry.last_ref_time
                    > self._limits_config.group_cooldown,
                )
                .values(
                    last_ref_time=current_time,
                    remain_tokens=self._limits_config.group_per_user_tokens_limit,
                )
            )
            await self._db_session.execute(regular_stmt)

        if supporter_user_ids:
            supporter_stmt = (
                update(UserGroupLimitEntry)
                .where(
                    UserGroupLimitEntry.user_id.in_(supporter_user_ids),
                    current_time - UserGroupLimitEntry.last_ref_time
                    > self._limits_config.group_cooldown,
                )
                .values(
                    last_ref_time=current_time,
                    remain_tokens=self._limits_config.group_per_support_user_tokens_limit,
                )
            )
            await self._db_session.execute(supporter_stmt)

        await self._db_session.commit()
