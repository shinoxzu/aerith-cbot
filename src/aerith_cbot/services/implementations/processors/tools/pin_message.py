import logging

from aiogram import Bot
from aiogram.types import Message

from aerith_cbot.services.implementations.processors.models import PinMessageParams

from .base import ToolCommand


class PinMessageToolCommand(ToolCommand):
    def __init__(self, bot: Bot) -> None:
        super().__init__()

        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, message: Message) -> str:
        params = PinMessageParams.model_validate_json(arguments)
        print(params)

        await self._bot.pin_chat_message(message.chat.id, params.message_id)

        return "название изменено"
