import logging

from aiogram import Bot
from pydantic import BaseModel

from aerith_cbot.services.abstractions import PermissionChecker

from . import ToolCommand


class KickUserParams(BaseModel):
    accessor_user_id: int
    user_id: int


class KickUserToolCommand(ToolCommand):
    def __init__(self, bot: Bot, permission_checker: PermissionChecker) -> None:
        super().__init__()

        self._bot = bot
        self._group_permission_checker = permission_checker
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = KickUserParams.model_validate_json(arguments)

        is_admin = await self._group_permission_checker.check_permissions(
            chat_id, params.accessor_user_id
        )

        if is_admin:
            await self._bot.ban_chat_member(chat_id, params.user_id)
            return "Пользователь исключен из чата."
        return "У пользователя не хватает прав для исключения другого участника."
