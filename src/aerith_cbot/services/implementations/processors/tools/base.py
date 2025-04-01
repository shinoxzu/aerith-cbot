from abc import ABC, abstractmethod


class ToolCommand(ABC):
    @abstractmethod
    async def execute(self, arguments: str, chat_id: int) -> str:
        pass
