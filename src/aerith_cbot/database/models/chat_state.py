from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChatState(Base):
    __tablename__ = "chat_states"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_focused: Mapped[bool] = mapped_column(nullable=False, default=False)
    listening_streak: Mapped[int] = mapped_column(nullable=False, default=0)
    ignoring_streak: Mapped[int] = mapped_column(nullable=False, default=0)
    sleeping_till: Mapped[int] = mapped_column(nullable=False, default=0)
    last_ignored_answer: Mapped[int] = mapped_column(nullable=False, default=0)

    def __repr__(self) -> str:
        return f"ChatState(\
        chat_id={self.chat_id}, \
        listening_streak={self.listening_streak}, \
        ignoring_streak={self.ignoring_streak}, \
        sleeping_till={self.sleeping_till}, \
        last_ignored_answer={self.last_ignored_answer})"
