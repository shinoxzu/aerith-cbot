from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column
from uuid_utils.compat import uuid7

from .base import Base


class Sticker(Base):
    __tablename__ = "stickers"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid7)
    file_id: Mapped[str] = mapped_column(nullable=False)
    emoji: Mapped[str] = mapped_column(nullable=False, index=True)
    set_name: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"Sticker(\
        id={self.id}, \
        file_id={self.file_id}, \
        emoji={self.emoji}, \
        set={self.set_name})"
