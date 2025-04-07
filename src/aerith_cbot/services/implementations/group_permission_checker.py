import logging

from aiogram import Bot, exceptions
from aiogram.enums import ChatMemberStatus

from aerith_cbot.services.abstractions import PermissionChecker


class GroupPermissionChecker(PermissionChecker):
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def check_permissions(self, chat_id: int, user_id: int) -> bool:
        try:
            chat_member = await self._bot.get_chat_member(chat_id, user_id)
        except exceptions.TelegramAPIError as err:
            self._logger.error("Cannot get chat %s admins cause of %s", chat_id, err, exc_info=err)
            return False

        if (
            chat_member.status == ChatMemberStatus.ADMINISTRATOR
            or chat_member.status == ChatMemberStatus.CREATOR
        ):
            return True
        return False
