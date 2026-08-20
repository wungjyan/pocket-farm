from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.models.production import QuantityUnit, WorkMethod


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
