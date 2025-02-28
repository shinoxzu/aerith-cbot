import asyncio
import warnings

from langchain_core._api.deprecation import LangChainDeprecationWarning
from mem0 import Memory

from aerith_cbot.services.abstractions import MemoryService

# some libriaries here are just painful with these warning so i just disable them  noqa
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)


class Mem0MemoryService(MemoryService):
    def __init__(self, memory: Memory) -> None:
        super().__init__()

        self._memory = memory

    async def remember(self, object_id: str, fact: str) -> None:
        await asyncio.to_thread(self._memory.add, messages=fact, user_id=object_id)

    async def search(self, object_id: str, query: str) -> str | None:
        result = await asyncio.to_thread(
            self._memory.search, query=query, user_id=object_id, limit=5
        )

        if result is None:
            return None

        print(result)

        return str(result)
