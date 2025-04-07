from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserPrivateLimitEntry(Base):
    __tablename__ = "users_private_limit_entries"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_ref_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    remain_tokens: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"UserPrivateLimitEntry(\
        user_id={self.user_id}, \
        last_ref_time={self.last_ref_time}, \
        remain_tokens={self.remain_tokens})"
