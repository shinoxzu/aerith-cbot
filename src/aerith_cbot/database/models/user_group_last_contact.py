from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserGroupLastContact(Base):
    __tablename__ = "user_group_last_contacts"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[bool] = mapped_column(BigInteger, primary_key=True)
    last_contacted_time: Mapped[int] = mapped_column(BigInteger, nullable=False)

    def __repr__(self) -> str:
        return f"UserGroupLastContact(\
        chat_id={self.chat_id}, \
        user_id={self.user_id}, \
        last_contacted_time={self.last_contacted_time})"
