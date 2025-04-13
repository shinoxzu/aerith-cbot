from pydantic import BaseModel


class MemoryToUpdate(BaseModel):
    id: str
    new_memory: str


class MemoriesStatus(BaseModel):
    new_memories: list[str]
    memories_to_update: list[MemoryToUpdate]
    memories_ids_to_delete: list[str]


class OpenAILLMConfig(BaseModel):
    api_key: str
    model: str
