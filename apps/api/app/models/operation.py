from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.production import WorkMethod
from app.models.user import utc_now_naive


class OperationTypeStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class OperationType(Base):
    __tablename__ = "operation_types"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OperationTypeStatus.ACTIVE, index=True
    )
    sort_order: Mapped[int] = mapped_column(INTEGER(unsigned=True), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )


class FarmOperation(Base):
    __tablename__ = "farm_operations"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    plot_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("plots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    production_id: Mapped[int | None] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("productions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    operation_type_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("operation_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    work_method: Mapped[str] = mapped_column(String(20), nullable=False, default=WorkMethod.MANUAL)
    operated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    operator_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )
