from sqlalchemy import JSON, UUID, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from uuid_utils.compat import uuid7

from .base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid7)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"Message(\
        id={self.id}, \
        chat_id={self.chat_id}, \
        data={self.data})"
