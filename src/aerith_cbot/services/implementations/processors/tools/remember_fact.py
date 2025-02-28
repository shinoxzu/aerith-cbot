import logging

from aiogram.types import Message

from aerith_cbot.services.abstractions import MemoryService
from aerith_cbot.services.implementations.processors.models import RememberFactParams

from .base import ToolCommand


class RememberFactToolCommand(ToolCommand):
    def __init__(self, memory_service: MemoryService) -> None:
        super().__init__()

        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, arguments: str, message: Message) -> str:
        params = RememberFactParams.model_validate_json(arguments)
        await self._memory_service.remember(str(params.user_id), params.fact)

        return "запомнила!"
