from pydantic import BaseModel


class ChromaOpenAIEmbeddingsConfig(BaseModel):
    api_key: str
    embedding_model: str


class ChromaConfig(BaseModel):
    host: str
    port: int
    openai_embeddings: ChromaOpenAIEmbeddingsConfig


class VectorStoreEntry(BaseModel):
    id: str
    text: str
    distance: float
    metadata: dict[str, str | int]


class VectorStoreEntryToUpdate(BaseModel):
    id: str
    text: str
    metadata: dict[str, str | int]
