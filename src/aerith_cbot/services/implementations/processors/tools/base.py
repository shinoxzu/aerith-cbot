from abc import ABC, abstractmethod


class ToolCommand(ABC):
    @abstractmethod
    async def execute(self, arguments: str, chat_id: int) -> str:
        pass


class ToolExecutionResult:
    def __init__(self, response: str) -> None:
        self.response = response

    def __str__(self) -> str:
        return f"ToolExecutionResult(response={self.response}"


class ToolCommandDispatcher(ABC):
    @abstractmethod
    async def execute_tool(self, name: str, arguments: str, chat_id: int) -> ToolExecutionResult:
        pass
