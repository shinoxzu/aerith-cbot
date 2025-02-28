import logging

from aiogram import Bot
from aiogram.types import Message

from aerith_cbot.services.implementations.processors.models import ChangeChatDescParams

from .base import ToolCommand


class ChangeChatDescToolCommand(ToolCommand):
    def __init__(self, bot: Bot) -> None:
        super().__init__()

        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, message: Message) -> str:
        params = ChangeChatDescParams.model_validate_json(arguments)
        print(params)

        await self._bot.set_chat_description(message.chat.id, params.description)

        return "описание изменено"
