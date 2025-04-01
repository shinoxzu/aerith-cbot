from typing import AsyncIterable

from dishka import Provider, Scope, provide
from mem0 import Memory
from openai import AsyncOpenAI

from aerith_cbot.config import (
    OpenAIConfig,
    QdrantConfig,
)


class ClientsProvider(Provider):
    @provide(scope=Scope.APP)
    async def openai_client(self, openai_config: OpenAIConfig) -> AsyncIterable[AsyncOpenAI]:
        client = AsyncOpenAI(api_key=openai_config.token)
        yield client
        await client.close()

    @provide(scope=Scope.APP)
    async def mem0_client(
        self,
        qdrant_config: QdrantConfig,
        openai_config: OpenAIConfig,
    ) -> Memory:
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": qdrant_config.collection_name,
                    "host": qdrant_config.host,
                    "port": qdrant_config.port,
                },
            },
            "llm": {
                "provider": "openai_structured",
                "config": {
                    "model": openai_config.memory_llm_model,
                    "api_key": openai_config.token,
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": openai_config.memory_embedder_model,
                    "api_key": openai_config.token,
                },
            },
            "version": "v1.1",
        }

        return Memory.from_config(config_dict=config)
