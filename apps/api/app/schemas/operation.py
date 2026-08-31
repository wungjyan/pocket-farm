from datetime import datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, Field, field_validator

from app.models.operation import OperationTypeStatus
from app.models.plot import AreaUnit
from app.models.production import ProductionStatus, WorkMethod


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("operatedAt must include a timezone offset.")
    return value


class CreateOperationRequest(BaseModel):
    operation_type_id: int = Field(
        gt=0,
        validation_alias=AliasChoices("operationTypeId", "operation_type_id"),
        serialization_alias="operationTypeId",
    )
    production_id: int | None = Field(
        ...,
        validation_alias=AliasChoices("productionId", "production_id"),
        serialization_alias="productionId",
    )
    work_method: WorkMethod = Field(
        default=WorkMethod.MANUAL,
        validation_alias=AliasChoices("workMethod", "work_method"),
        serialization_alias="workMethod",
    )
    operated_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("operatedAt", "operated_at"),
        serialization_alias="operatedAt",
    )
    operator_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("operatorId", "operator_id"),
        serialization_alias="operatorId",
    )
    remark: str | None = Field(default=None, max_length=1000)

    @field_validator("operated_at")
    @classmethod
    def validate_operated_at_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)


class UpdateOperationRequest(BaseModel):
    production_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("productionId", "production_id"),
        serialization_alias="productionId",
    )
    operation_type_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("operationTypeId", "operation_type_id"),
        serialization_alias="operationTypeId",
    )
    work_method: WorkMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("workMethod", "work_method"),
        serialization_alias="workMethod",
    )
    operated_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("operatedAt", "operated_at"),
        serialization_alias="operatedAt",
    )
    operator_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("operatorId", "operator_id"),
        serialization_alias="operatorId",
    )
    remark: str | None = Field(default=None, max_length=1000)

    @field_validator("operated_at")
    @classmethod
    def validate_operated_at_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)


class OperationResponse(BaseModel):
    id: int
    plot_id: int = Field(serialization_alias="plotId")
    production_id: int | None = Field(default=None, serialization_alias="productionId")
    operation_type: "OperationTypeResponse" = Field(serialization_alias="operationType")
    work_method: WorkMethod = Field(serialization_alias="workMethod")
    operated_at: datetime = Field(serialization_alias="operatedAt")
    operator_id: int = Field(serialization_alias="operatorId")
    created_by: int = Field(serialization_alias="createdBy")
    remark: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class OperationPage(BaseModel):
    items: list[OperationResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class OperationTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    status: OperationTypeStatus
    sort_order: int = Field(serialization_alias="sortOrder")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class OperationTypePage(BaseModel):
    items: list[OperationTypeResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class FarmOperationSummaryResponse(BaseModel):
    id: int
    plot_id: int = Field(serialization_alias="plotId")
    plot_name: str = Field(serialization_alias="plotName")
    plot_area_value: Decimal | None = Field(default=None, serialization_alias="plotAreaValue")
    plot_area_unit: AreaUnit | None = Field(default=None, serialization_alias="plotAreaUnit")
    production_id: int | None = Field(default=None, serialization_alias="productionId")
    operation_type_id: int = Field(serialization_alias="operationTypeId")
    operation_type_name: str = Field(serialization_alias="operationTypeName")
    operated_at: datetime = Field(serialization_alias="operatedAt")
    species_name: str | None = Field(default=None, serialization_alias="speciesName")
    production_status: ProductionStatus | None = Field(
        default=None,
        serialization_alias="productionStatus",
    )


class FarmOperationSummaryPage(BaseModel):
    items: list[FarmOperationSummaryResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class OperationTypeOption(BaseModel):
    id: int
    name: str


class OperationFilterOptionsResponse(BaseModel):
    types: list[OperationTypeOption]
