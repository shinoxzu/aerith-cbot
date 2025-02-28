import logging

from aiogram import Bot
from aiogram.types import Message

from aerith_cbot.services.implementations.processors.models import KickUserParams

from .base import ToolCommand


class KickUserToolCommand(ToolCommand):
    def __init__(self, bot: Bot) -> None:
        super().__init__()

        self._bot = bot
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, message: Message) -> str:
        params = KickUserParams.model_validate_json(arguments)
        print(params)

        await self._bot.ban_chat_member(message.chat.id, params.user_id)

        return "пользователь заблокирован изменено"
