import logging

from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from aerith_cbot.services.abstractions import MemoryService

from .base import ToolCommand
from .change_chat_desc import ChangeChatDescToolCommand
from .change_chat_name import ChangeChatNameToolCommand
from .fetch_info import FetchInfoToolCommand
from .ignore_message import IgnoreMessageToolCommand
from .kick_user import KickUserToolCommand
from .pin_message import PinMessageToolCommand
from .remember_fact import RememberFactToolCommand
from .wait_for_user_end import WaitForUserEndToolCommand


class ToolCommandDispatcher:
    def __init__(
        self,
        bot: Bot,
        db_session: AsyncSession,
        memory_service: MemoryService,
    ):
        self._tools: dict[str, ToolCommand] = {
            "remember_fact": RememberFactToolCommand(memory_service),
            "ignore_message": IgnoreMessageToolCommand(db_session),
            "wait_for_user_end": WaitForUserEndToolCommand(db_session),
            "pin_message": PinMessageToolCommand(bot),
            "fetch_info": FetchInfoToolCommand(memory_service),
            "change_chat_name": ChangeChatNameToolCommand(bot),
            "change_chat_description": ChangeChatDescToolCommand(bot),
            "kick_user": KickUserToolCommand(bot),
        }
        self._logger = logging.getLogger(__name__)

    async def execute_tool(self, name: str, arguments: str, message: Message) -> str:
        self._logger.debug("Running tool %s(%s) for message %s", name, arguments, str(message))
        return await self._tools[name].execute(arguments, message)
