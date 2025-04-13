from abc import ABC, abstractmethod


class UserContextProvider(ABC):
    @abstractmethod
    async def provide_context(self, chat_id: int) -> str:
        raise NotImplementedError

    @abstractmethod
    async def update_context(self, user_id: int, context: str) -> None:
        raise NotImplementedError
