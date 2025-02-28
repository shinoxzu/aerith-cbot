import logging

from aiogram.types import Message

from aerith_cbot.services.abstractions import MemoryService
from aerith_cbot.services.implementations.processors.models import FetchInfoParams

from .base import ToolCommand


class FetchInfoToolCommand(ToolCommand):
    def __init__(self, memory_service: MemoryService) -> None:
        super().__init__()

        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, message: Message) -> str:
        params = FetchInfoParams.model_validate_json(arguments)
        result = await self._memory_service.search(params.topic.value, message.text or "")

        return str(result)
