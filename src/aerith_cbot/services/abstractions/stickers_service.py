from abc import ABC, abstractmethod

from .models import StickerDTO


class StickersService(ABC):
    @abstractmethod
    async def load(self, stickers: list[StickerDTO]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, emoji: str) -> str | None:
        """Return file_id of the sticker"""
        raise NotImplementedError
