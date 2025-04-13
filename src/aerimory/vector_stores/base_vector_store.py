from abc import ABC, abstractmethod

from aerimory.types import VectorStoreEntry, VectorStoreEntryToUpdate


class BaseVectorStore(ABC):
    @abstractmethod
    async def search(self, object_id: str, query: str, limit: int) -> list[VectorStoreEntry]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, object_id: str) -> list[VectorStoreEntry]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, object_id: str, text: str, metadata: dict[str, str | int]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, object_id: str, entry_ids: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, object_id: str, entries_to_update: list[VectorStoreEntryToUpdate]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def count(self, object_id: str) -> int:
        raise NotImplementedError
