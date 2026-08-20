from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utc_now_naive


class ProductionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class PlantingStandard(StrEnum):
    NORMAL = "NORMAL"
    GREEN = "GREEN"
    ORGANIC = "ORGANIC"


class PlantingMethod(StrEnum):
    TRANSPLANT = "TRANSPLANT"
    DIRECT_SEEDING = "DIRECT_SEEDING"


class WorkMethod(StrEnum):
    MANUAL = "MANUAL"
    MECHANICAL = "MECHANICAL"


class QuantityUnit(StrEnum):
    KG = "KG"
    HEAD = "HEAD"
    FEATHER = "FEATHER"
    PIECE = "PIECE"
    PLANT = "PLANT"
    TAIL = "TAIL"


class Production(Base):
    __tablename__ = "productions"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    plot_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("plots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    species_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("species.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variety: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ProductionStatus.ACTIVE)
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    ended_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    planting_standard: Mapped[str | None] = mapped_column(String(20), nullable=True)
    planting_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    work_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expected_harvest_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_yield_per_mu: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    initial_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    plant_spacing_cm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    entry_age_days: Mapped[int | None] = mapped_column(INTEGER(unsigned=True), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )
