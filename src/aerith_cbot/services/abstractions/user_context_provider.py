from abc import ABC, abstractmethod


class UserContextProvider(ABC):
    @abstractmethod
    async def provide_chat_users_context(self, chat_id: int) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def provide_private_user_context(self, user_id: int) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def update_context(self, user_id: int, context: str) -> None:
        raise NotImplementedError
