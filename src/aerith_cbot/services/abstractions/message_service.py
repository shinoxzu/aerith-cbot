from abc import ABC, abstractmethod


class MessageService(ABC):
    @abstractmethod
    async def fetch_messages(self, chat_id: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    async def add_messages(self, chat_id: int, messages: list[dict]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def shorten_history(self, chat_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def shorten_full_history_without_media(self, chat_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self, chat_id: int) -> None:
        raise NotImplementedError
