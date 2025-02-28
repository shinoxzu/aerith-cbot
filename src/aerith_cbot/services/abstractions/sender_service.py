from abc import ABC, abstractmethod

from aiogram.types import Message

from .models import ModelResponse


class SenderService(ABC):
    @abstractmethod
    async def send(self, message: Message, response: ModelResponse) -> None:
        raise NotImplementedError
