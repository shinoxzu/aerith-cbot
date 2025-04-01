import logging

from aiogram import Bot
from pydantic import BaseModel

from . import ToolCommand


class PinMessageParams(BaseModel):
    message_id: int
    accessor_user_id: int


class PinMessageToolCommand(ToolCommand):
    def __init__(self, bot: Bot) -> None:
        super().__init__()

        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = PinMessageParams.model_validate_json(arguments)

        await self._bot.pin_chat_message(chat_id, params.message_id)

        return "Сообщение закреплено."
