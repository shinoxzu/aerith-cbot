from abc import ABC, abstractmethod

from .models import ModelResponse


class SenderService(ABC):
    @abstractmethod
    async def send(self, chat_id: int, response: ModelResponse) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_refusal(self, chat_id: int, refusal: str) -> None:
        raise NotImplementedError
