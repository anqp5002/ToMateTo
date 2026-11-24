"""T04: provider push tokens never appear in repr/log output."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class UserDevice(Base):
    __tablename__ = "user_devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    push_token: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == user_id
