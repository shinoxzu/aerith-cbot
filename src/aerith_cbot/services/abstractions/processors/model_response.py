from abc import ABC, abstractmethod


class ModelResponseProcessor(ABC):
    @abstractmethod
    async def process(self, chat_id: int, response_raw: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def process_refusal(self, chat_id: int, refusal: str) -> None:
        raise NotImplementedError
