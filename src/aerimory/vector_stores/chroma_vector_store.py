import logging
import time
import uuid

import chromadb
import openai
from chromadb.api import AsyncClientAPI

from aerimory.types import ChromaConfig, VectorStoreEntry, VectorStoreEntryToUpdate
from aerimory.vector_stores import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    MAX_CACHE_SIZE = 80

    def __init__(self, config: ChromaConfig) -> None:
        super().__init__()

        self._config = config
        self._chroma_client: None | AsyncClientAPI = None
        self._openai_client = openai.AsyncOpenAI(api_key=config.openai_embeddings.api_key)
        self._embeddings_cache: dict[str, tuple[list[float], int]] = {}
        self._logger = logging.getLogger(__name__)

    async def _get_new_chroma_client(self) -> AsyncClientAPI:
        return await chromadb.AsyncHttpClient(host=self._config.host, port=self._config.port)

    async def _get_cached_embedding(self, text: str) -> list[float]:
        if len(self._embeddings_cache) >= ChromaVectorStore.MAX_CACHE_SIZE:
            sorted_by_add_time = sorted(self._embeddings_cache.items(), key=lambda x: x[1][1])[:10]
            for oldest_entry_key, _ in sorted_by_add_time:
                del self._embeddings_cache[oldest_entry_key]

        if text not in self._embeddings_cache:
            embedding = await self._openai_client.embeddings.create(
                input=text, model=self._config.openai_embeddings.embedding_model
            )
            self._embeddings_cache[text] = (embedding.data[0].embedding, int(time.time()))

        return self._embeddings_cache[text][0]

    def _search_result_to_entry(
        self, search_result: chromadb.QueryResult
    ) -> list[VectorStoreEntry]:
        if len(search_result["ids"][0]) == 0:
            return []

        entries = []

        ids = search_result["ids"][0]
        documents = (search_result["documents"] or [])[0]
        distances = (search_result["distances"] or [])[0]
        metadatas = (search_result["metadatas"] or [])[0]

        for document, distance, memory_id, metadata in zip(documents, distances, ids, metadatas):
            entry = VectorStoreEntry(
                id=memory_id,
                text=document,
                distance=distance,
                metadata={k: str(v) for k, v in metadata.items()},
            )
            entries.append(entry)

        return entries

    def _get_result_to_entry(self, get_result: chromadb.GetResult) -> list[VectorStoreEntry]:
        if len(get_result["ids"][0]) == 0:
            return []

        entries = []

        ids = get_result["ids"]
        documents = get_result["documents"] or []
        metadatas = get_result["metadatas"] or []

        for document, memory_id, metadata in zip(documents, ids, metadatas):
            entry = VectorStoreEntry(
                id=memory_id,
                text=document,
                distance=0,
                metadata={k: str(v) for k, v in metadata.items()},
            )
            entries.append(entry)

        return entries

    async def search(self, object_id: str, query: str, limit: int) -> list[VectorStoreEntry]:
        if self._chroma_client is None:
            self._chroma_client = await self._get_new_chroma_client()

        collection = await self._chroma_client.get_or_create_collection(
            name=f"user-{object_id}-memories"
        )

        query_embedding = await self._get_cached_embedding(query)
        raw_search_result = await collection.query(
            query_embeddings=[query_embedding], query_texts=[query], n_results=limit
        )

        self._logger.info(
            "Search result for object %s with query %s: %s", object_id, query, raw_search_result
        )

        return self._search_result_to_entry(raw_search_result)

    async def get_all(self, object_id: str) -> list[VectorStoreEntry]:
        if self._chroma_client is None:
            self._chroma_client = await self._get_new_chroma_client()

        collection = await self._chroma_client.get_or_create_collection(
            name=f"user-{object_id}-memories"
        )

        raw_get_result = await collection.get()

        return self._get_result_to_entry(raw_get_result)

    async def create(self, object_id: str, text: str, metadata: dict[str, str | int]) -> None:
        if self._chroma_client is None:
            self._chroma_client = await self._get_new_chroma_client()

        collection = await self._chroma_client.get_or_create_collection(
            name=f"user-{object_id}-memories"
        )

        text_embedding = await self._get_cached_embedding(text)
        await collection.add(
            embeddings=[text_embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())],
        )

    async def update(
        self, object_id: str, entries_to_update: list[VectorStoreEntryToUpdate]
    ) -> None:
        if self._chroma_client is None:
            self._chroma_client = await self._get_new_chroma_client()

        collection = await self._chroma_client.get_or_create_collection(
            name=f"user-{object_id}-memories"
        )

        await collection.update(
            ids=[e.id for e in entries_to_update],
            embeddings=[await self._get_cached_embedding(e.text) for e in entries_to_update],
            documents=[e.text for e in entries_to_update],
            metadatas=[e.metadata for e in entries_to_update],
        )

    async def remove(self, object_id: str, entry_ids: list[str]) -> None:
        if self._chroma_client is None:
            self._chroma_client = await self._get_new_chroma_client()

        collection = await self._chroma_client.get_or_create_collection(
            name=f"user-{object_id}-memories"
        )

        await collection.delete([entry_id for entry_id in entry_ids])

    async def count(self, object_id: str) -> int:
        if self._chroma_client is None:
            self._chroma_client = await self._get_new_chroma_client()

        collection = await self._chroma_client.get_or_create_collection(
            name=f"user-{object_id}-memories"
        )
        return await collection.count()
