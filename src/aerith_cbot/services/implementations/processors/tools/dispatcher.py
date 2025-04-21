import logging

import aiohttp
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions import (
    MemoryService,
    PermissionChecker,
    UserContextProvider,
    VoiceTranscriber,
)

from .base import ToolCommand, ToolCommandDispatcher, ToolExecutionResult
from .members import (
    ChangeChatDescToolCommand,
    ChangeChatNameToolCommand,
    FetchInfoToolCommand,
    FetchUserInfoToolCommand,
    GetChatInfoToolCommand,
    KickUserToolCommand,
    PinMessageToolCommand,
    RememberUserInfoToolCommand,
    ThinkToolCommand,
    UnfocusChatToolCommand,
    UpdateUserContextCommand,
)


class DefaultToolCommandDispatcher(ToolCommandDispatcher):
    def __init__(
        self,
        bot: Bot,
        db_session: AsyncSession,
        memory_service: MemoryService,
        permission_checker: PermissionChecker,
        llm_config: LLMConfig,
        context_provider: UserContextProvider,
        voice_transcriber: VoiceTranscriber,
        client_session: aiohttp.ClientSession,
    ):
        self._tools: dict[str, ToolCommand] = {
            "think": ThinkToolCommand(),
            "remember_user_info": RememberUserInfoToolCommand(memory_service, llm_config),
            "fetch_info": FetchInfoToolCommand(memory_service, llm_config),
            "fetch_user_info": FetchUserInfoToolCommand(memory_service, llm_config),
            "pin_message": PinMessageToolCommand(bot, llm_config),
            "change_chat_name": ChangeChatNameToolCommand(bot, permission_checker, llm_config),
            "change_chat_description": ChangeChatDescToolCommand(
                bot, permission_checker, llm_config
            ),
            "kick_user": KickUserToolCommand(bot, permission_checker, llm_config),
            "update_user_context": UpdateUserContextCommand(context_provider, llm_config),
            "unfocus_chat": UnfocusChatToolCommand(db_session, llm_config),
            "get_chat_info": GetChatInfoToolCommand(
                bot, llm_config, voice_transcriber, client_session
            ),
        }
        self._logger = logging.getLogger(__name__)

    async def execute_tool(self, name: str, arguments: str, chat_id: int) -> ToolExecutionResult:
        self._logger.info(
            "Calling tool %s in chat %s with params %s",
            name,
            chat_id,
            arguments,
        )

        try:
            result = await self._tools[name].execute(arguments, chat_id)
        except Exception as e:
            self._logger.error("Cannot execute tool", exc_info=e)
            result = "Произошла ошибка. Не вышло выполнить указанное действие"

        self._logger.info("Result for tool %s in chat %s is: %s", name, chat_id, result)

        return ToolExecutionResult(result)
