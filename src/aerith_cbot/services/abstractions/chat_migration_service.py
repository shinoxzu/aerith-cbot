from abc import ABC, abstractmethod


class ChatMigrationService(ABC):
    @abstractmethod
    async def update(self, old_chat_id: int, chat_id: int) -> None:
        raise NotImplementedError
