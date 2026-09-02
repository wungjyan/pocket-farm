from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utc_now_naive


class AIDailyTurnUsage(Base):
    """Daily per-user AI request counter; chat content is intentionally not stored."""

    __tablename__ = "ai_daily_turn_usages"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "usage_date",
            name="uq_ai_daily_turn_usages_user_id_usage_date",
        ),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    turn_count: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )


class AIConversation(Base):
    """A private, farm-scoped conversation owned by one user."""

    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("ix_ai_conversations_user_farm_updated", "user_id", "farm_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    farm_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )


class AIMessage(Base):
    """Persisted user or assistant content; raw tool payloads are intentionally excluded."""

    __tablename__ = "ai_messages"
    __table_args__ = (Index("ix_ai_messages_conversation_id_id", "conversation_id", "id"),)

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    references: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    candidates: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
