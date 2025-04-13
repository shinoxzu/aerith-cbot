from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserPersonalContext(Base):
    __tablename__ = "user_personal_context"

    user_id: Mapped[bool] = mapped_column(BigInteger, primary_key=True)
    context: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"UserPersonalContext(\
        user_id={self.user_id}, \
        context={self.context})"
