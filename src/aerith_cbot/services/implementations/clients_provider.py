from dishka import Provider, Scope, provide
from mem0 import Memory
from openai import AsyncOpenAI

from aerith_cbot.config import Neo4jConfig, OpenAIConfig, QdrantConfig


class ClientsProvider(Provider):
    @provide(scope=Scope.APP)
    async def openai_client(self, openai_config: OpenAIConfig) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=openai_config.token)

    @provide(scope=Scope.APP)
    async def mem0_client(
        self,
        neo4j_config: Neo4jConfig,
        qdrant_config: QdrantConfig,
    ) -> Memory:
        config = {
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": neo4j_config.url,
                    "username": neo4j_config.username,
                    "password": neo4j_config.password,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": qdrant_config.collection_name,
                    "host": qdrant_config.host,
                    "port": qdrant_config.port,
                },
            },
            "llm": {
                "provider": "openai",
                "config": {"model": "gpt-4o-mini", "api_key": "as"},
            },
            "embedder": {
                "provider": "openai",
                "config": {"model": "text-embedding-3-small", "api_key": "as"},
            },
            "version": "v1.1",
        }

        return Memory.from_config(config_dict=config)
