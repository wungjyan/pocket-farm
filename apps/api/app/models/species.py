from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user import utc_now_naive


class Industry(StrEnum):
    AGRICULTURE = "AGRICULTURE"
    FORESTRY = "FORESTRY"
    LIVESTOCK = "LIVESTOCK"
    FISHERY = "FISHERY"


class IndividualUnit(StrEnum):
    HEAD = "HEAD"
    FEATHER = "FEATHER"
    PIECE = "PIECE"
    PLANT = "PLANT"
    TAIL = "TAIL"


class Species(Base):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    individual_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
