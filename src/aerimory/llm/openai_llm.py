import logging
import time

import openai

from aerimory.llm.base_llm import (
    DEFAULT_SYSTEM_RESOLVE_CONTRADICTIONS_PROMPT,
    DEFAULT_USER_RESOLVE_CONTRADICTIONS_PROMPT,
    BaseLLM,
)
from aerimory.types import MemoriesStatus, Memory, OpenAILLMConfig


class OpenAILLM(BaseLLM):
    def __init__(self, config: OpenAILLMConfig):
        self._config = config
        self._openai_client = openai.AsyncOpenAI(api_key=config.api_key)
        self._logger = logging.getLogger(__name__)

    async def resolve_contradictions(
        self, new_memory: str, old_memories: list[Memory]
    ) -> MemoriesStatus:
        similar_memories_text = ""
        for old_memory in old_memories:
            created_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(old_memory.created_at))
            updated_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(old_memory.updated_at))
            metadata_str = f"Создано: {created_time}, Обновлено: {updated_time}"

            similar_memories_text += (
                f"ID: {old_memory.id}, {metadata_str}\n\n{old_memory.memory}\n\n\n"
            )

        try:
            response = await self._openai_client.beta.chat.completions.parse(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_RESOLVE_CONTRADICTIONS_PROMPT},
                    {
                        "role": "user",
                        "content": DEFAULT_USER_RESOLVE_CONTRADICTIONS_PROMPT.format(
                            new=new_memory, old=similar_memories_text
                        ),
                    },
                ],
                response_format=MemoriesStatus,
            )

            self._logger.debug("llm response: %s", response)

            if response.choices[0].message.parsed is None:
                return MemoriesStatus(
                    memories_to_update=[], memories_ids_to_delete=[], new_memories=[]
                )

            return response.choices[0].message.parsed
        except openai.APIError:
            return MemoriesStatus(memories_to_update=[], memories_ids_to_delete=[], new_memories=[])
