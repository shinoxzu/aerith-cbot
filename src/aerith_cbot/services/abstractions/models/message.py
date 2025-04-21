from pydantic import BaseModel


class InputChat(BaseModel):
    id: int
    name: str


class InputUser(BaseModel):
    id: int
    name: str


class InputMessage(BaseModel):
    id: int
    chat: InputChat
    sender: InputUser
    reply_message: "InputMessage | None"
    photo_url: str | None
    voice_url: str | None
    text: str | None
    date: str
    is_aerith_called: bool
    is_aerith_joined: bool
    meta: str | None
