import logging

from pydantic import BaseModel

from aerith_cbot.services.abstractions import MemoryService

from . import ToolCommand


class RememberUserInfoParams(BaseModel):
    info: str
    user_id: int


class RememberUserInfoToolCommand(ToolCommand):
    def __init__(self, memory_service: MemoryService) -> None:
        super().__init__()

        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = RememberUserInfoParams.model_validate_json(arguments)
        await self._memory_service.remember(str(params.user_id), params.info)

        return "Информация сохранена."
