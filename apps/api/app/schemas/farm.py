from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.models.farm import FarmMemberRole
from app.models.plot import AreaUnit, PlotType
from app.schemas.harvest import HarvestResponse
from app.schemas.operation import OperationResponse
from app.schemas.production import ProductionResponse


class CreateFarmRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    region: Annotated[str | None, Field(default=None, max_length=100)]


class UpdateFarmRequest(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=100)]
    region: Annotated[str | None, Field(default=None, max_length=100)]
    ai_enabled: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("aiEnabled", "ai_enabled"),
        serialization_alias="aiEnabled",
    )

    @model_validator(mode="after")
    def validate_ai_enabled(self) -> "UpdateFarmRequest":
        if "ai_enabled" in self.model_fields_set and self.ai_enabled is None:
            raise ValueError("aiEnabled cannot be null.")
        return self


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_code: str = Field(serialization_alias="farmCode")
    name: str
    region: str | None = None
    ai_enabled: bool = Field(serialization_alias="aiEnabled")
    created_by: int = Field(serialization_alias="createdBy")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    my_role: FarmMemberRole | None = Field(default=None, serialization_alias="myRole")


class FarmPage(BaseModel):
    items: list[FarmResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class CreateMemberRequest(BaseModel):
    phone_number: str = Field(
        validation_alias=AliasChoices("phoneNumber", "phone_number"),
        min_length=11,
        max_length=11,
        pattern=r"^1[3-9]\d{9}$",
    )
    role: FarmMemberRole = FarmMemberRole.MEMBER


class UpdateMemberRequest(BaseModel):
    role: FarmMemberRole


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int = Field(serialization_alias="userId")
    nickname: str | None = None
    role: FarmMemberRole
    joined_at: datetime = Field(serialization_alias="joinedAt")


class MemberPage(BaseModel):
    items: list[MemberResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class CreatePlotRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    plot_type: PlotType = Field(
        validation_alias=AliasChoices("type", "plotType", "plot_type"),
        serialization_alias="type",
    )
    area_value: Annotated[Decimal, Field(gt=0)] = Field(
        validation_alias=AliasChoices("areaValue", "area_value"),
        serialization_alias="areaValue",
    )
    area_unit: AreaUnit = Field(
        validation_alias=AliasChoices("areaUnit", "area_unit"),
        serialization_alias="areaUnit",
    )
    boundary: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_area_and_boundary(self) -> "CreatePlotRequest":
        _validate_boundary(self.boundary)
        return self


class UpdatePlotRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    plot_type: PlotType | None = Field(
        default=None,
        validation_alias=AliasChoices("type", "plotType", "plot_type"),
        serialization_alias="type",
    )
    area_value: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("areaValue", "area_value"),
        serialization_alias="areaValue",
    )
    area_unit: AreaUnit | None = Field(
        default=None,
        validation_alias=AliasChoices("areaUnit", "area_unit"),
        serialization_alias="areaUnit",
    )
    boundary: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_fields(self) -> "UpdatePlotRequest":
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null.")
        area_fields = {"area_value", "area_unit"} & self.model_fields_set
        if area_fields and area_fields != {"area_value", "area_unit"}:
            raise ValueError("areaValue and areaUnit must be updated together.")
        _validate_boundary(self.boundary)
        return self


class PlotResponse(BaseModel):
    id: int
    farm_id: int = Field(serialization_alias="farmId")
    name: str
    plot_type: PlotType | None = Field(default=None, serialization_alias="type")
    area_value: Decimal | None = Field(default=None, serialization_alias="areaValue")
    area_unit: AreaUnit | None = Field(default=None, serialization_alias="areaUnit")
    area_m2: Decimal | None = Field(default=None, serialization_alias="areaM2")
    boundary: dict[str, Any] | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class PlotPage(BaseModel):
    items: list[PlotResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class PlotSummaryFilter(StrEnum):
    ALL = "ALL"
    IDLE = "IDLE"
    SPECIES = "SPECIES"


class ActiveSpeciesResponse(BaseModel):
    id: int
    name: str


class PlotSummaryResponse(PlotResponse):
    active_species: list[ActiveSpeciesResponse] = Field(serialization_alias="activeSpecies")


class PlotSummaryPage(BaseModel):
    items: list[PlotSummaryResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class PlotFilterOptionsResponse(BaseModel):
    active_species: list[ActiveSpeciesResponse] = Field(serialization_alias="activeSpecies")
    idle_plot_count: int = Field(serialization_alias="idlePlotCount")


class PlotDetailResponse(BaseModel):
    plot: PlotResponse
    active_productions: list[ProductionResponse] = Field(serialization_alias="activeProductions")
    ended_productions: list[ProductionResponse] = Field(serialization_alias="endedProductions")
    operations: list[OperationResponse]
    operation_total: int = Field(serialization_alias="operationTotal")
    harvests: list[HarvestResponse]
    harvest_total: int = Field(serialization_alias="harvestTotal")


def _validate_boundary(boundary: dict[str, Any] | None) -> None:
    if boundary is not None and boundary.get("coordinateSystem") != "GCJ02":
        raise ValueError('boundary.coordinateSystem must be "GCJ02".')
