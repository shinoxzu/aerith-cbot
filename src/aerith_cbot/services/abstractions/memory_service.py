from abc import ABC, abstractmethod

from aerith_cbot.services.abstractions.models import SearchMessage


class MemoryService(ABC):
    @abstractmethod
    async def remember(self, object_id: str, fact: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, object_id: str, query: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def search_users(self, messages: list[SearchMessage]) -> str | None:
        raise NotImplementedError
