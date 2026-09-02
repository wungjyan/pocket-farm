from datetime import datetime
from enum import StrEnum

from sqlalchemy import BOOLEAN, CHAR, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utc_now_naive


class FarmMemberRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    farm_code: Mapped[str] = mapped_column(CHAR(6), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_enabled: Mapped[bool] = mapped_column(
        BOOLEAN,
        nullable=False,
        default=True,
        server_default="1",
    )
    created_by: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )


class FarmMember(Base):
    __tablename__ = "farm_members"
    __table_args__ = (
        UniqueConstraint("farm_id", "user_id", name="uq_farm_members_farm_id_user_id"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
