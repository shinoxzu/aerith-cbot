import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.services.abstractions import MemoryService
from aerith_cbot.services.implementations import GroupPermissionChecker

from .base import ToolCommand
from .members import (
    ChangeChatDescToolCommand,
    ChangeChatNameToolCommand,
    FetchInfoToolCommand,
    FetchUserInfoToolCommand,
    IgnoreMessageToolCommand,
    KickUserToolCommand,
    PinMessageToolCommand,
    RememberUserInfoToolCommand,
    WaitForUserEndToolCommand,
)


class ToolExecutionResult:
    def __init__(self, response: str, stop: bool) -> None:
        self.response = response
        self.stop = stop

    def __str__(self) -> str:
        return f"ToolExecutionResult(response={self.response}, stop={self.stop})"


class ToolCommandDispatcher:
    def __init__(
        self,
        bot: Bot,
        db_session: AsyncSession,
        memory_service: MemoryService,
        group_permission_checker: GroupPermissionChecker,
    ):
        self._tools: dict[str, ToolCommand] = {
            "ignore_message": IgnoreMessageToolCommand(db_session),
            "wait_for_user_end": WaitForUserEndToolCommand(db_session),
            "remember_user_info": RememberUserInfoToolCommand(memory_service),
            "fetch_info": FetchInfoToolCommand(memory_service),
            "fetch_user_info": FetchUserInfoToolCommand(memory_service),
            "pin_message": PinMessageToolCommand(bot),
            "change_chat_name": ChangeChatNameToolCommand(bot, group_permission_checker),
            "change_chat_description": ChangeChatDescToolCommand(bot, group_permission_checker),
            "kick_user": KickUserToolCommand(bot, group_permission_checker),
        }
        self._logger = logging.getLogger(__name__)

    async def execute_tool(self, name: str, arguments: str, chat_id: int) -> ToolExecutionResult:
        self._logger.debug("Running tool %s(%s) for chat %s", name, arguments, chat_id)

        result = await self._tools[name].execute(arguments, chat_id)
        stop = name in ("ignore_message", "wait_for_user_end")

        return ToolExecutionResult(result, stop)
