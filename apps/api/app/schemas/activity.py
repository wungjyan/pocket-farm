from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.plot import AreaUnit
from app.models.production import QuantityUnit
from app.models.species import Industry

FarmActivityType = Literal[
    "PRODUCTION_STARTED",
    "PRODUCTION_ENDED",
    "OPERATION_CREATED",
    "HARVEST_CREATED",
]


class FarmActivityResponse(BaseModel):
    type: FarmActivityType
    occurred_at: datetime = Field(serialization_alias="occurredAt")
    production_id: int | None = Field(default=None, serialization_alias="productionId")
    operation_id: int | None = Field(default=None, serialization_alias="operationId")
    harvest_id: int | None = Field(default=None, serialization_alias="harvestId")
    plot_id: int = Field(serialization_alias="plotId")
    plot_name: str = Field(serialization_alias="plotName")
    plot_area_value: Decimal | None = Field(default=None, serialization_alias="plotAreaValue")
    plot_area_unit: AreaUnit | None = Field(default=None, serialization_alias="plotAreaUnit")
    species_name: str | None = Field(default=None, serialization_alias="speciesName")
    industry: Industry | None = None
    operation_type_name: str | None = Field(default=None, serialization_alias="operationTypeName")
    quantity: Decimal | None = None
    unit: QuantityUnit | None = None
    operator_name: str | None = Field(default=None, serialization_alias="operatorName")


class FarmActivityListResponse(BaseModel):
    items: list[FarmActivityResponse]
