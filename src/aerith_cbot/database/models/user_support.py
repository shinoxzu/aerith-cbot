from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserSupport(Base):
    __tablename__ = "user_supporters"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    end_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_notified: Mapped[bool] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"UserSupport(\
        user_id={self.user_id}, \
        end_timestamp={self.end_timestamp}, \
        is_notified={self.is_notified})"
