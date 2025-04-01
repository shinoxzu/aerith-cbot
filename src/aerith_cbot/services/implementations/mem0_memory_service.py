import asyncio
import logging

# from langchain_core._api.deprecation import LangChainDeprecationWarning
from mem0 import Memory

from aerith_cbot.services.abstractions import MemoryService
from aerith_cbot.services.abstractions.models import SearchMessage

# some libriaries here are just painful with these warning so i just disable them noqa
# warnings.filterwarnings("ignore", category=DeprecationWarning)
# warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


class Mem0MemoryService(MemoryService):
    MIN_SCORE = 0.2

    def __init__(self, memory: Memory) -> None:
        super().__init__()

        self._memory = memory
        self._logger = logging.getLogger(__name__)

    async def remember(self, object_id: str, fact: str) -> None:
        self._logger.info("Remembering in %s: %s", object_id, fact)
        await asyncio.to_thread(self._memory.add, messages=fact, user_id=object_id)

    async def search(self, object_id: str, query: str) -> str | None:
        result_data = await asyncio.to_thread(
            self._memory.search, query=query, user_id=object_id, limit=3
        )

        if result_data is None or (not result_data["results"] and not result_data["relations"]):
            return None

        result = ""

        for r in result_data["results"]:
            if r["score"] > Mem0MemoryService.MIN_SCORE:
                result += f"{r['memory']}\n"

        return result if result else None

    async def search_users(self, messages: list[SearchMessage]) -> str | None:
        search_results = await asyncio.gather(
            *[self.search(str(msg.user_id), msg.query) for msg in messages]
        )

        search_results_unique: dict[int, list[str]] = {}

        for msg, search_result in zip(messages, search_results):
            if search_result is not None:
                if msg.user_id not in search_results_unique:
                    search_results_unique[msg.user_id] = []

                search_results_unique[msg.user_id].append(search_result)

        if search_results_unique:
            result_string = (
                "Информация о пользователях. Используй ТОЛЬКО если нужно и НЕ упоминай просто так!"
            )
            for user_id, r in search_results_unique.items():
                result_string += f"\n\nИнформация об user_id={user_id}:\n{'\n'.join(r)}"

            return result_string
