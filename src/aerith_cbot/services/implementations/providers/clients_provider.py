from typing import AsyncIterable

from dishka import Provider, Scope, provide
from openai import AsyncOpenAI

from aerimory import AerimoryClient
from aerimory.llm import OpenAILLM
from aerimory.types import ChromaConfig as AerimoryChromaConfig
from aerimory.types import ChromaOpenAIEmbeddingsConfig, OpenAILLMConfig
from aerimory.vector_stores import ChromaVectorStore
from aerith_cbot.config import (
    ChromaConfig,
    OpenAIConfig,
)


class ClientsProvider(Provider):
    @provide(scope=Scope.APP)
    async def openai_client(self, openai_config: OpenAIConfig) -> AsyncIterable[AsyncOpenAI]:
        client = AsyncOpenAI(api_key=openai_config.token)
        yield client
        await client.close()

    @provide(scope=Scope.APP)
    async def aerimory_client(
        self,
        chroma_config: ChromaConfig,
        openai_config: OpenAIConfig,
    ) -> AerimoryClient:
        open_ai_llm_config = OpenAILLMConfig(
            api_key=openai_config.token, model=openai_config.memory_llm_model
        )
        aeimory_chroma_config = AerimoryChromaConfig(
            host=chroma_config.host,
            port=chroma_config.port,
            openai_embeddings=ChromaOpenAIEmbeddingsConfig(
                api_key=openai_config.token, embedding_model=openai_config.memory_embedder_model
            ),
        )

        client = AerimoryClient(
            vector_store=ChromaVectorStore(aeimory_chroma_config), llm=OpenAILLM(open_ai_llm_config)
        )

        return client
