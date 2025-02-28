from pydantic import BaseModel


class StickerDTO(BaseModel):
    file_id: str
    emoji: str
    set_name: str
