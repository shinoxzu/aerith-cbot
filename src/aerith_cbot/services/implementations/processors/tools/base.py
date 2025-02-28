from abc import ABC, abstractmethod

from aiogram.types import Message


class ToolCommand(ABC):
    @abstractmethod
    async def execute(self, arguments: str, message: Message) -> str:
        pass
