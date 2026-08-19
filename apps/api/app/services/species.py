from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.species import Industry, Species


async def list_species(
    session: AsyncSession,
    *,
    industry: Industry | None,
    keyword: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Species], int]:
    filters = []
    if industry is not None:
        filters.append(Species.industry == industry)
    if keyword:
        filters.append(Species.name.like(f"%{keyword}%"))

    total = await session.scalar(select(func.count()).select_from(Species).where(*filters))
    result = await session.execute(
        select(Species)
        .where(*filters)
        .order_by(Species.industry.asc(), Species.name.asc(), Species.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars()), int(total or 0)
