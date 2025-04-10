import logging

from aerimory import AerimoryClient
from aerith_cbot.config import LLMConfig
from aerith_cbot.services.abstractions import MemoryService


class AerimoryMemoryService(MemoryService):
    def __init__(self, client: AerimoryClient, llm_config: LLMConfig) -> None:
        super().__init__()

        self._llm_config = llm_config
        self._client = client
        self._logger = logging.getLogger(__name__)

    async def remember(self, object_id: str, fact: str) -> None:
        self._logger.info("Remembering for %s: %s", object_id, fact)

        # user can't have more than 70 memories
        await self._client.add_memory(object_id, fact, overall_limit=70)

    async def search(self, object_id: str, query: str) -> str | None:
        memories = await self._client.search(object_id, query, limit=5)

        result = ""
        for memory in memories:
            result += f"{memory.memory}\n\n"

        return result if result else None
