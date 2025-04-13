import logging
import time

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

        # user can't have more than 100 memories
        await self._client.add_memory(object_id, fact, overall_limit=100)

    async def search(self, object_id: str, query: str) -> str | None:
        memories = await self._client.search(object_id, query, limit=5)

        result = ""
        for memory in memories:
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(memory.created_at))
            updated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(memory.updated_at))
            result += (
                f"(дата создания: {created_at}, дата изменения: {updated_at}): {memory.memory}\n\n"
            )

        return result if result else None
