from aiogram.filters import BaseFilter
from aiogram.types import Message
from dishka import FromDishka

from aerith_cbot.config import BotConfig


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message, config: FromDishka[BotConfig]) -> bool:
        if message.from_user is None:
            return False
        return message.from_user.id in config.admin_ids
