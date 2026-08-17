from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now_naive() -> datetime:
    """Return the current UTC time without a timezone for MySQL DATETIME."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )
