from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utc_now_naive


class PlotType(StrEnum):
    FIELD = "FIELD"
    PADDY = "PADDY"
    GREENHOUSE = "GREENHOUSE"
    ORCHARD = "ORCHARD"
    FOREST = "FOREST"
    POND = "POND"
    BARN = "BARN"
    OTHER = "OTHER"


class AreaUnit(StrEnum):
    MU = "MU"
    SQUARE_METER = "SQUARE_METER"
    HECTARE = "HECTARE"


class Plot(Base):
    __tablename__ = "plots"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    farm_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("farms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plot_type: Mapped[str | None] = mapped_column("type", String(20), nullable=True)
    area_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    area_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    boundary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now_naive,
        onupdate=utc_now_naive,
        nullable=False,
    )
