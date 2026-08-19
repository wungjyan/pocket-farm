from datetime import datetime

from pydantic import BaseModel, Field

from app.models.species import IndividualUnit, Industry


class SpeciesResponse(BaseModel):
    id: int
    name: str
    industry: Industry
    individual_unit: IndividualUnit = Field(serialization_alias="individualUnit")
    created_at: datetime = Field(serialization_alias="createdAt")


class SpeciesPage(BaseModel):
    items: list[SpeciesResponse]
    page: int
    page_size: int = Field(serialization_alias="pageSize")
    total: int
