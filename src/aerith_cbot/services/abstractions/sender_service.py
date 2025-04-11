from abc import ABC, abstractmethod

from .models import ModelResponse


class SenderService(ABC):
    @abstractmethod
    async def send_model_response(self, chat_id: int, response: ModelResponse) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_model_refusal(self, chat_id: int, refusal: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_ignoring(self, chat_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_support_end_notify(self, chat_id: int) -> None:
        raise NotImplementedError
