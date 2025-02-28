from enum import Enum

from pydantic import BaseModel


class ChangeChatDescParams(BaseModel):
    description: str
    accessor_user_id: int


class ChangeChatNameParams(BaseModel):
    name: str
    accessor_user_id: int


class PinMessageParams(BaseModel):
    message_id: int
    accessor_user_id: int


class KickUserParams(BaseModel):
    accessor_user_id: int
    user_id: int


class RememberFactParams(BaseModel):
    fact: str
    user_id: int


class InfoTopic(Enum):
    aerith = "aerith"
    news = "news"


class FetchInfoParams(BaseModel):
    topic: InfoTopic
