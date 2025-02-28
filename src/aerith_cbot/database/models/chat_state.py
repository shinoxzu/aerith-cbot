from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChatState(Base):
    __tablename__ = "chat_states"

    chat_id: Mapped[BigInteger] = mapped_column(BigInteger, primary_key=True)
    is_answering: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_focused: Mapped[bool] = mapped_column(nullable=False, default=False)
    listening_streak: Mapped[int] = mapped_column(nullable=False, default=0)
    ignoring_streak: Mapped[int] = mapped_column(nullable=False, default=0)  # >10, is_focused=False

    def __repr__(self) -> str:
        return f"ChatState(\
        chat_id={self.chat_id}, \
        is_answering={self.is_answering}, \
        is_focused={self.is_focused}, \
        listening_streak={self.listening_streak}, \
        ignoring_streak={self.ignoring_streak})"
