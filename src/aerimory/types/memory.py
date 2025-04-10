from pydantic import BaseModel


class Memory(BaseModel):
    id: str
    memory: str
    distance: float
    created_at: int
    updated_at: int
