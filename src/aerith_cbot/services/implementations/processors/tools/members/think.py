from pydantic import BaseModel

from . import ToolCommand


class ThinkParams(BaseModel):
    thoughts: str


class ThinkToolCommand(ToolCommand):
    def __init__(self) -> None:
        super().__init__()

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = ThinkParams.model_validate_json(arguments)
        return params.thoughts
