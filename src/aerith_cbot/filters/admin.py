from aiogram.filters import BaseFilter
from aiogram.types import Message
from dishka import FromDishka

from aerith_cbot.config import Config


class AdminFilter(BaseFilter):
    def __init__(self, config: FromDishka[Config]) -> None:
        self.config = config

    async def __call__(self, message: Message) -> bool:
        if message.from_user is None:
            return False
        return message.from_user.id in self.config.bot.admin_ids
