import logging

from aiogram import Bot
from pydantic import BaseModel

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions import PermissionChecker

from . import ToolCommand


class ChangeChatNameParams(BaseModel):
    name: str
    accessor_user_id: int


class ChangeChatNameToolCommand(ToolCommand):
    def __init__(
        self, bot: Bot, permission_checker: PermissionChecker, llm_config: LLMConfig
    ) -> None:
        super().__init__()

        self._bot = bot
        self._group_permission_checker = permission_checker
        self._logger = logging.getLogger(__name__)
        self._llm_config = llm_config

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = ChangeChatNameParams.model_validate_json(arguments)

        is_admin = await self._group_permission_checker.check_permissions(
            chat_id, params.accessor_user_id
        )

        if is_admin:
            await self._bot.set_chat_title(chat_id, params.name)
            return self._llm_config.additional_instructions.name_changed
        return self._llm_config.additional_instructions.user_hasnt_rights
