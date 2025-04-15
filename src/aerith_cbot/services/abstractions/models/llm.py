import typing

from pydantic import BaseModel


class ModelInputUser(BaseModel):
    user_id: int
    name: str


class ModelInputMessage(BaseModel):
    """This model describes the DTO that will be sent to the model in a user prompt."""

    message_id: int
    sender: ModelInputUser
    reply_message: typing.Optional["ModelInputMessage"] = None
    text: str | None = None
    date: str
    meta: str | None


class ModelResponse(BaseModel):
    text: list[str]
    sticker: typing.Optional[str]
    reply_to_message_id: typing.Optional[int]
