import logging

from aiogram import Bot
from pydantic import BaseModel

from aerith_cbot.services.implementations import GroupPermissionChecker

from . import ToolCommand


class ChangeChatDescParams(BaseModel):
    description: str
    accessor_user_id: int


class ChangeChatDescToolCommand(ToolCommand):
    def __init__(self, bot: Bot, group_permission_checker: GroupPermissionChecker) -> None:
        super().__init__()

        self._bot = bot
        self._group_permission_checker = group_permission_checker
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = ChangeChatDescParams.model_validate_json(arguments)

        is_admin = await self._group_permission_checker.check_permissions(
            chat_id, params.accessor_user_id
        )

        if is_admin:
            await self._bot.set_chat_description(chat_id, params.description)
            return "Описание изменено."
        return "У пользователя не хватает прав для смены описания чата."
