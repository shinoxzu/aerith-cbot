from abc import ABC, abstractmethod


class LimitsService(ABC):
    @abstractmethod
    async def check_private_limit(self, user_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def check_group_limit(self, user_id: int, chat_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def subtract_private_tokens(self, user_id: int, tokens_count: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def subtract_group_tokens(self, chat_id: int, tokens_count: int) -> None:
        raise NotImplementedError
