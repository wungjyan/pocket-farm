from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.species import IndividualUnit, Industry
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.species import SpeciesPage, SpeciesResponse
from app.services.species import list_species

router = APIRouter(tags=["species"])


def _species_response(species) -> SpeciesResponse:
    return SpeciesResponse(
        id=species.id,
        name=species.name,
        industry=Industry(species.industry),
        individual_unit=IndividualUnit(species.individual_unit),
        created_at=species.created_at,
    )


@router.get("/species", response_model=ApiResponse[SpeciesPage])
async def get_species(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    industry: Industry | None = None,
    keyword: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> ApiResponse[SpeciesPage]:
    species, total = await list_species(
        session,
        industry=industry,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success_response(
        data=SpeciesPage(
            items=[_species_response(item) for item in species],
            page=page,
            page_size=page_size,
            total=total,
        )
    )
