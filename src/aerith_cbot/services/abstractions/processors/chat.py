from abc import ABC, abstractmethod

from aerith_cbot.services.abstractions.models import ChatType


class ChatProcessor(ABC):
    @abstractmethod
    async def process(self, chat_id: int, chat_type: ChatType) -> None:
        raise NotImplementedError
