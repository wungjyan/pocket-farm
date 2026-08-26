from datetime import date, datetime
from decimal import Decimal

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.models.production import (
    PlantingMethod,
    PlantingStandard,
    ProductionStatus,
    WorkMethod,
)
from app.models.species import IndividualUnit, Industry


class CreateProductionRequest(BaseModel):
    species_id: int = Field(
        gt=0,
        validation_alias=AliasChoices("speciesId", "species_id"),
        serialization_alias="speciesId",
    )
    variety: str | None = Field(default=None, max_length=100)
    started_on: date = Field(
        validation_alias=AliasChoices("startedOn", "started_on"),
        serialization_alias="startedOn",
    )
    planting_standard: PlantingStandard | None = Field(
        default=None,
        validation_alias=AliasChoices("plantingStandard", "planting_standard"),
        serialization_alias="plantingStandard",
    )
    planting_method: PlantingMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("plantingMethod", "planting_method"),
        serialization_alias="plantingMethod",
    )
    work_method: WorkMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("workMethod", "work_method"),
        serialization_alias="workMethod",
    )
    expected_harvest_on: date | None = Field(
        default=None,
        validation_alias=AliasChoices("expectedHarvestOn", "expected_harvest_on"),
        serialization_alias="expectedHarvestOn",
    )
    expected_yield_per_mu: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("expectedYieldPerMu", "expected_yield_per_mu"),
        serialization_alias="expectedYieldPerMu",
    )
    initial_quantity: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("initialQuantity", "initial_quantity"),
        serialization_alias="initialQuantity",
    )
    plant_spacing_cm: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("plantSpacingCm", "plant_spacing_cm"),
        serialization_alias="plantSpacingCm",
    )
    entry_age_days: int | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("entryAgeDays", "entry_age_days"),
        serialization_alias="entryAgeDays",
    )
    remark: str | None = Field(default=None, max_length=1000)


class UpdateProductionRequest(BaseModel):
    plot_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("plotId", "plot_id"),
        serialization_alias="plotId",
    )
    species_id: int | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("speciesId", "species_id"),
        serialization_alias="speciesId",
    )
    variety: str | None = Field(default=None, max_length=100)
    started_on: date | None = Field(
        default=None,
        validation_alias=AliasChoices("startedOn", "started_on"),
        serialization_alias="startedOn",
    )
    planting_standard: PlantingStandard | None = Field(
        default=None,
        validation_alias=AliasChoices("plantingStandard", "planting_standard"),
        serialization_alias="plantingStandard",
    )
    planting_method: PlantingMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("plantingMethod", "planting_method"),
        serialization_alias="plantingMethod",
    )
    work_method: WorkMethod | None = Field(
        default=None,
        validation_alias=AliasChoices("workMethod", "work_method"),
        serialization_alias="workMethod",
    )
    expected_harvest_on: date | None = Field(
        default=None,
        validation_alias=AliasChoices("expectedHarvestOn", "expected_harvest_on"),
        serialization_alias="expectedHarvestOn",
    )
    expected_yield_per_mu: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("expectedYieldPerMu", "expected_yield_per_mu"),
        serialization_alias="expectedYieldPerMu",
    )
    initial_quantity: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("initialQuantity", "initial_quantity"),
        serialization_alias="initialQuantity",
    )
    plant_spacing_cm: Decimal | None = Field(
        default=None,
        gt=0,
        validation_alias=AliasChoices("plantSpacingCm", "plant_spacing_cm"),
        serialization_alias="plantSpacingCm",
    )
    entry_age_days: int | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("entryAgeDays", "entry_age_days"),
        serialization_alias="entryAgeDays",
    )
    remark: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_required_fields(self) -> "UpdateProductionRequest":
        for field_name in {"plot_id", "species_id", "started_on"} & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")
        return self


class EndProductionRequest(BaseModel):
    ended_on: date | None = Field(
        default=None,
        validation_alias=AliasChoices("endedOn", "ended_on"),
        serialization_alias="endedOn",
    )


class ProductionResponse(BaseModel):
    id: int
    plot_id: int = Field(serialization_alias="plotId")
    species_id: int = Field(serialization_alias="speciesId")
    species_name: str = Field(serialization_alias="speciesName")
    industry: Industry
    individual_unit: IndividualUnit = Field(serialization_alias="individualUnit")
    variety: str | None = None
    status: ProductionStatus
    started_on: date = Field(serialization_alias="startedOn")
    ended_on: date | None = Field(default=None, serialization_alias="endedOn")
    planting_standard: PlantingStandard | None = Field(
        default=None,
        serialization_alias="plantingStandard",
    )
    planting_method: PlantingMethod | None = Field(
        default=None,
        serialization_alias="plantingMethod",
    )
    work_method: WorkMethod | None = Field(default=None, serialization_alias="workMethod")
    expected_harvest_on: date | None = Field(
        default=None,
        serialization_alias="expectedHarvestOn",
    )
    expected_yield_per_mu: Decimal | None = Field(
        default=None,
        serialization_alias="expectedYieldPerMu",
    )
    initial_quantity: Decimal | None = Field(default=None, serialization_alias="initialQuantity")
    plant_spacing_cm: Decimal | None = Field(
        default=None,
        serialization_alias="plantSpacingCm",
    )
    entry_age_days: int | None = Field(default=None, serialization_alias="entryAgeDays")
    remark: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ProductionPage(BaseModel):
    items: list[ProductionResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int


class FarmProductionResponse(BaseModel):
    id: int
    plot_id: int = Field(serialization_alias="plotId")
    plot_name: str = Field(serialization_alias="plotName")
    species_id: int = Field(serialization_alias="speciesId")
    species_name: str = Field(serialization_alias="speciesName")
    industry: Industry
    individual_unit: IndividualUnit = Field(serialization_alias="individualUnit")
    variety: str | None = None
    status: ProductionStatus
    started_on: date = Field(serialization_alias="startedOn")
    ended_on: date | None = Field(default=None, serialization_alias="endedOn")
    initial_quantity: Decimal | None = Field(default=None, serialization_alias="initialQuantity")


class FarmProductionPage(BaseModel):
    items: list[FarmProductionResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int
