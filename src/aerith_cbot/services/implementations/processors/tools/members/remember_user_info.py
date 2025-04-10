import asyncio
import logging

from pydantic import BaseModel

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions import MemoryService

from . import ToolCommand


class RememberUserInfoParams(BaseModel):
    user_id: int
    info: str


class RememberUserInfoToolCommand(ToolCommand):
    def __init__(self, memory_service: MemoryService, llm_config: LLMConfig) -> None:
        super().__init__()

        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)
        self._llm_config = llm_config

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = RememberUserInfoParams.model_validate_json(arguments)

        # dont wait for the task to complete for optimization purposes
        asyncio.create_task(self._memory_service.remember(str(params.user_id), params.info))

        return self._llm_config.additional_instructions.info_saved

    async def _safe_remember(self, object_id: str, info: str):
        try:
            await self._memory_service.remember(object_id, info)
        except Exception as e:
            self._logger.exception(
                "Cannot create memory for %s cause of %s", object_id, e, exc_info=e
            )
