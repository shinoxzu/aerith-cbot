import typing

from aiogram.filters import BaseFilter
from aiogram.types import Message


class SenderFilter(BaseFilter):
    def __init__(self, sender_type: typing.Literal["chat", "user"]) -> None:
        self.sender_type = sender_type

    async def __call__(self, message: Message) -> bool:
        if self.sender_type == "chat":
            return message.sender_chat is not None
        elif self.sender_type == "user":
            return message.from_user is not None and message.sender_chat is None

        return False
