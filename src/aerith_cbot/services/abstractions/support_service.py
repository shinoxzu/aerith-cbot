from abc import ABC, abstractmethod

from aerith_cbot.services.abstractions.models import UserSupport


class SupportService(ABC):
    @abstractmethod
    async def is_active_supporter(self, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def fetch_supporter(self, user_id: int) -> UserSupport | None:
        raise NotImplementedError

    @abstractmethod
    async def prolong_support(self, user_id: int, interval: int) -> None:
        raise NotImplementedError
