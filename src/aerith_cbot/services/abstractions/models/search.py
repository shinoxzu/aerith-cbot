from pydantic import BaseModel


class SearchMessage(BaseModel):
    user_id: int
    query: str
