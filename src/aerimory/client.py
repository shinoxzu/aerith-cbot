import logging
import time

from aerimory.llm import BaseLLM
from aerimory.types import Memory, VectorStoreEntry, VectorStoreEntryToUpdate
from aerimory.vector_stores import BaseVectorStore


class AerimoryClient:
    def __init__(self, vector_store: BaseVectorStore, llm: BaseLLM) -> None:
        self._vector_store = vector_store
        self._llm = llm
        self._logger = logging.getLogger(__name__)

    def _entries_to_memories(self, entries: list[VectorStoreEntry]) -> list[Memory]:
        memories = []

        for entry in entries:
            memories.append(
                Memory(
                    id=entry.id,
                    memory=entry.text,
                    distance=entry.distance,
                    created_at=int(entry.metadata["created_at"]),
                    updated_at=int(entry.metadata["updated_at"]),
                )
            )

        return memories

    async def add_memory(self, object_id: str, memory: str, overall_limit: int) -> None:
        self._logger.info("Adding memory for object %s: %s", object_id, memory)

        current_memories_count = await self._vector_store.count(object_id)

        self._logger.debug(
            "Current memories count for user %s: %s, limit: %s",
            object_id,
            current_memories_count,
            overall_limit,
        )

        if current_memories_count >= overall_limit:
            self._logger.info(
                "Memory limit reached for user %s, removing oldest memories", object_id
            )

            all_entries = await self._vector_store.get_all(object_id)
            all_memories = self._entries_to_memories(all_entries)

            # we delete 0.1x memories of overall limit more then needed when limit occurs
            ub = current_memories_count - overall_limit + round(overall_limit * 0.3)

            oldest_memories = sorted(all_memories, key=lambda x: x.updated_at)[:ub]
            if oldest_memories:
                self._logger.debug(
                    "Deleting %s oldest memories for user %s", len(oldest_memories), object_id
                )
                await self._vector_store.remove(object_id, [mem.id for mem in oldest_memories])

        similar_entries = await self._vector_store.search(object_id, memory, 5)
        similar_memories = self._entries_to_memories(similar_entries)

        self._logger.debug(
            "Checking for contradictions against similar memories: %s", similar_memories
        )
        memory_status = await self._llm.resolve_contradictions(memory, similar_memories)

        self._logger.debug("LLM contradiction resolution result: %s", memory_status)

        if memory_status.memories_ids_to_delete:
            await self._vector_store.remove(object_id, memory_status.memories_ids_to_delete)

        for new_memory in memory_status.new_memories:
            await self._vector_store.create(
                object_id,
                new_memory,
                metadata={"created_at": int(time.time()), "updated_at": int(time.time())},
            )

        entries_to_update = []
        for memory_to_update in memory_status.memories_to_update:
            entry_to_update = VectorStoreEntryToUpdate(
                id=memory_to_update.id,
                text=memory_to_update.new_memory,
                metadata={"updated_at": int(time.time())},
            )
            entries_to_update.append(entry_to_update)

        if entries_to_update:
            await self._vector_store.update(object_id, entries_to_update)

    async def search(self, object_id: str, query: str, limit: int = 5) -> list[Memory]:
        entries = await self._vector_store.search(object_id, query, limit)
        memories = self._entries_to_memories(entries)

        return memories
