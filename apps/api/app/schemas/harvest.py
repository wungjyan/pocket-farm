from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.models.plot import AreaUnit
from app.models.production import ProductionStatus, QuantityUnit, WorkMethod
from app.models.species import Industry


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("harvestedAt must include a timezone offset.")
    return value


class CreateHarvestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=4)
    work_method: WorkMethod = Field(
        default=WorkMethod.MANUAL,
        validation_alias=AliasChoices("workMethod", "work_method"),
        serialization_alias="workMethod",
    )
    harvested_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("harvestedAt", "harvested_at"),
        serialization_alias="harvestedAt",
    )
    operator_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("operatorId", "operator_id"),
        serialization_alias="operatorId",
    )
    product_name: str | None = Field(
        default=None,
        max_length=100,
        validation_alias=AliasChoices("productName", "product_name"),
        serialization_alias="productName",
    )
    grade: str | None = Field(default=None, max_length=100)
    remark: str | None = Field(default=None, max_length=1000)

    @field_validator("harvested_at")
    @classmethod
    def validate_harvested_at_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)


class UpdateHarvestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=14,
        decimal_places=4,
    )
    work_method: WorkMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("workMethod", "work_method"),
        serialization_alias="workMethod",
    )
    harvested_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("harvestedAt", "harvested_at"),
        serialization_alias="harvestedAt",
    )
    operator_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("operatorId", "operator_id"),
        serialization_alias="operatorId",
    )
    product_name: str | None = Field(
        default=None,
        max_length=100,
        validation_alias=AliasChoices("productName", "product_name"),
        serialization_alias="productName",
    )
    grade: str | None = Field(default=None, max_length=100)
    remark: str | None = Field(default=None, max_length=1000)

    @field_validator("harvested_at")
    @classmethod
    def validate_harvested_at_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)


class HarvestResponse(BaseModel):
    id: int
    production_id: int = Field(serialization_alias="productionId")
    quantity: Decimal
    unit: QuantityUnit
    work_method: WorkMethod = Field(serialization_alias="workMethod")
    harvested_at: datetime = Field(serialization_alias="harvestedAt")
    operator_id: int = Field(serialization_alias="operatorId")
    created_by: int = Field(serialization_alias="createdBy")
    product_name: str | None = Field(default=None, serialization_alias="productName")
    grade: str | None = None
    remark: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class HarvestPage(BaseModel):
    items: list[HarvestResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class FarmHarvestSummaryResponse(BaseModel):
    id: int
    production_id: int = Field(serialization_alias="productionId")
    production_status: ProductionStatus = Field(serialization_alias="productionStatus")
    plot_id: int = Field(serialization_alias="plotId")
    plot_name: str = Field(serialization_alias="plotName")
    plot_area_value: Decimal | None = Field(default=None, serialization_alias="plotAreaValue")
    plot_area_unit: AreaUnit | None = Field(default=None, serialization_alias="plotAreaUnit")
    species_id: int = Field(serialization_alias="speciesId")
    species_name: str = Field(serialization_alias="speciesName")
    industry: Industry
    quantity: Decimal
    unit: QuantityUnit
    harvested_at: datetime = Field(serialization_alias="harvestedAt")
    product_name: str | None = Field(default=None, serialization_alias="productName")
    operator_id: int = Field(serialization_alias="operatorId")
    operator_name: str | None = Field(default=None, serialization_alias="operatorName")
    created_by: int = Field(serialization_alias="createdBy")
    creator_name: str | None = Field(default=None, serialization_alias="creatorName")


class FarmHarvestSummaryPage(BaseModel):
    items: list[FarmHarvestSummaryResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class HarvestSpeciesOption(BaseModel):
    id: int
    name: str


class HarvestFilterOptionsResponse(BaseModel):
    species: list[HarvestSpeciesOption]
