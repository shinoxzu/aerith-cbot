import logging
from enum import Enum

from pydantic import BaseModel

from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions import MemoryService

from . import ToolCommand


class InfoTopic(Enum):
    aerith = "aerith"
    news = "news"


class FetchInfoParams(BaseModel):
    topic: InfoTopic
    query: str


class FetchInfoToolCommand(ToolCommand):
    def __init__(self, memory_service: MemoryService, llm_config: LLMConfig) -> None:
        super().__init__()

        self._memory_service = memory_service
        self._logger = logging.getLogger(__name__)
        self._llm_config = llm_config

    async def execute(self, arguments: str, chat_id: int) -> str:
        params = FetchInfoParams.model_validate_json(arguments)
        result = await self._memory_service.search(params.topic.value, params.query)

        return result or self._llm_config.additional_instructions.info_not_found
