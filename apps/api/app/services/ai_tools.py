import json
from dataclasses import dataclass
from datetime import UTC
from decimal import Decimal
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production import ProductionStatus
from app.schemas.ai import AIReference
from app.services.activity import list_farm_activities
from app.services.harvest import list_farm_harvests
from app.services.operation import list_farm_operations, list_operation_types
from app.services.plot import get_plot_detail, get_plot_with_member, list_plots
from app.services.production import list_farm_productions
from app.services.species import list_species

TOOL_RESULT_LIMIT = 20
MAX_REFERENCES = 10


class _ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchPlotsArgs(_ToolArgs):
    keyword: str | None = Field(default=None, min_length=1, max_length=100)


class GetPlotDetailArgs(_ToolArgs):
    plot_id: int = Field(gt=0)


class ListProductionsArgs(_ToolArgs):
    status: ProductionStatus | None = None


class EmptyArgs(_ToolArgs):
    pass


ToolArgs: TypeAlias = SearchPlotsArgs | GetPlotDetailArgs | ListProductionsArgs | EmptyArgs


@dataclass(frozen=True)
class ToolExecution:
    data: dict[str, Any]
    references: list[AIReference]
    candidates: list[AIReference]


def tool_definitions() -> list[dict[str, Any]]:
    return [
        _tool_definition("search_plots", "按名称查询当前农场的地块。", SearchPlotsArgs),
        _tool_definition(
            "get_plot_detail",
            "读取当前农场某个已明确选择的地块详情。",
            GetPlotDetailArgs,
        ),
        _tool_definition("list_productions", "查询当前农场的种养记录。", ListProductionsArgs),
        _tool_definition("list_operations", "查询当前农场最近的农事记录。", EmptyArgs),
        _tool_definition("list_harvests", "查询当前农场最近的收获记录。", EmptyArgs),
        _tool_definition("list_recent_activities", "查询当前农场最近的生产动态。", EmptyArgs),
        _tool_definition("list_species", "查询系统种养种类选项。", SearchPlotsArgs),
        _tool_definition("list_operation_types", "查询系统农事类型选项。", EmptyArgs),
    ]


def _tool_definition(name: str, description: str, arguments: type[BaseModel]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": arguments.model_json_schema(),
        },
    }


def parse_tool_arguments(name: str, arguments: str) -> ToolArgs:
    schema_by_name: dict[str, type[ToolArgs]] = {
        "search_plots": SearchPlotsArgs,
        "get_plot_detail": GetPlotDetailArgs,
        "list_productions": ListProductionsArgs,
        "list_operations": EmptyArgs,
        "list_harvests": EmptyArgs,
        "list_recent_activities": EmptyArgs,
        "list_species": SearchPlotsArgs,
        "list_operation_types": EmptyArgs,
    }
    schema = schema_by_name.get(name)
    if schema is None:
        raise ValueError("unsupported tool")
    try:
        raw_arguments = json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid tool arguments") from exc
    return schema.model_validate(raw_arguments)


async def execute_tool(
    session: AsyncSession,
    *,
    name: str,
    arguments: ToolArgs,
    farm_id: int,
    user_id: int,
) -> ToolExecution:
    if name == "search_plots" and isinstance(arguments, SearchPlotsArgs):
        return await _search_plots(
            session,
            farm_id=farm_id,
            user_id=user_id,
            keyword=arguments.keyword,
        )
    if name == "get_plot_detail" and isinstance(arguments, GetPlotDetailArgs):
        return await _get_plot_detail(
            session,
            farm_id=farm_id,
            user_id=user_id,
            plot_id=arguments.plot_id,
        )
    if name == "list_productions" and isinstance(arguments, ListProductionsArgs):
        return await _list_productions(
            session,
            farm_id=farm_id,
            user_id=user_id,
            status=arguments.status,
        )
    if name == "list_operations" and isinstance(arguments, EmptyArgs):
        return await _list_operations(session, farm_id=farm_id, user_id=user_id)
    if name == "list_harvests" and isinstance(arguments, EmptyArgs):
        return await _list_harvests(session, farm_id=farm_id, user_id=user_id)
    if name == "list_recent_activities" and isinstance(arguments, EmptyArgs):
        return await _list_recent_activities(session, farm_id=farm_id, user_id=user_id)
    if name == "list_species" and isinstance(arguments, SearchPlotsArgs):
        return await _list_species(session, keyword=arguments.keyword)
    if name == "list_operation_types" and isinstance(arguments, EmptyArgs):
        return await _list_operation_types(session)
    raise ValueError("unsupported tool")


async def _search_plots(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    keyword: str | None,
) -> ToolExecution:
    plots, _ = await list_plots(
        session,
        farm_id=farm_id,
        user_id=user_id,
        page=1,
        page_size=TOOL_RESULT_LIMIT,
        keyword=keyword,
    )
    references = [_plot_reference(plot.id, plot.name) for plot in plots]
    candidates = references if keyword is not None and len(references) > 1 else []
    return ToolExecution(
        data={
            "plots": [
                {
                    "id": plot.id,
                    "name": plot.name,
                    "type": plot.plot_type,
                    "area_value": _number(plot.area_value),
                    "area_unit": plot.area_unit,
                }
                for plot in plots
            ]
        },
        references=references,
        candidates=candidates,
    )


async def _get_plot_detail(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    plot_id: int,
) -> ToolExecution:
    plot, _ = await get_plot_with_member(session, plot_id=plot_id, user_id=user_id)
    if plot.farm_id != farm_id:
        return ToolExecution(data={"found": False}, references=[], candidates=[])
    detail = await get_plot_detail(session, plot_id=plot_id, user_id=user_id)
    productions = [
        {
            "id": production.id,
            "species": species.name,
            "variety": production.variety,
            "status": production.status,
            "started_on": production.started_on.isoformat(),
        }
        for production, species in [*detail.active_productions, *detail.ended_productions]
    ]
    references = [_plot_reference(detail.plot.id, detail.plot.name)] + [
        _production_reference(item[0].id, item[1].name, item[0].variety)
        for item in [*detail.active_productions, *detail.ended_productions]
    ]
    return ToolExecution(
        data={
            "found": True,
            "plot": {
                "id": detail.plot.id,
                "name": detail.plot.name,
                "type": detail.plot.plot_type,
                "area_value": _number(detail.plot.area_value),
                "area_unit": detail.plot.area_unit,
            },
            "productions": productions,
        },
        references=references,
        candidates=[],
    )


async def _list_productions(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    status: ProductionStatus | None,
) -> ToolExecution:
    productions, _ = await list_farm_productions(
        session,
        farm_id=farm_id,
        user_id=user_id,
        industry=None,
        status=status,
        species_id=None,
        page=1,
        page_size=TOOL_RESULT_LIMIT,
    )
    return ToolExecution(
        data={
            "productions": [
                {
                    "id": production.id,
                    "plot_id": plot.id,
                    "plot_name": plot.name,
                    "species": species.name,
                    "industry": species.industry,
                    "variety": production.variety,
                    "status": production.status,
                    "started_on": production.started_on.isoformat(),
                    "ended_on": production.ended_on.isoformat() if production.ended_on else None,
                    "initial_quantity": _number(production.initial_quantity),
                    "individual_unit": species.individual_unit,
                }
                for production, plot, species in productions
            ]
        },
        references=[
            _production_reference(production.id, species.name, production.variety)
            for production, _, species in productions
        ],
        candidates=[],
    )


async def _list_operations(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
) -> ToolExecution:
    operations, _ = await list_farm_operations(
        session,
        farm_id=farm_id,
        user_id=user_id,
        operation_type_id=None,
        page=1,
        page_size=TOOL_RESULT_LIMIT,
    )
    return ToolExecution(
        data={
            "operations": [
                {
                    "id": operation.id,
                    "plot_id": plot.id,
                    "plot_name": plot.name,
                    "production_id": operation.production_id,
                    "operation_type": operation_type.name,
                    "operated_at": _datetime(operation.operated_at),
                    "species": species.name if species else None,
                }
                for operation, plot, operation_type, _, species in operations
            ]
        },
        references=[
            AIReference(
                kind="OPERATION",
                id=operation.id,
                label=f"{operation_type.name} · {plot.name}",
                route=f"/pages/operations/detail?operationId={operation.id}",
            )
            for operation, plot, operation_type, _, _ in operations
        ],
        candidates=[],
    )


async def _list_harvests(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
) -> ToolExecution:
    harvests, _ = await list_farm_harvests(
        session,
        farm_id=farm_id,
        user_id=user_id,
        industry=None,
        species_id=None,
        page=1,
        page_size=TOOL_RESULT_LIMIT,
    )
    return ToolExecution(
        data={
            "harvests": [
                {
                    "id": harvest.id,
                    "production_id": production.id,
                    "plot_id": plot.id,
                    "plot_name": plot.name,
                    "species": species.name,
                    "quantity": _number(harvest.quantity),
                    "unit": harvest.unit,
                    "harvested_at": _datetime(harvest.harvested_at),
                }
                for harvest, production, plot, species, _, _ in harvests
            ]
        },
        references=[
            AIReference(
                kind="HARVEST",
                id=harvest.id,
                label=f"{species.name} · {plot.name}",
                route=f"/pages/harvests/detail?harvestId={harvest.id}",
            )
            for harvest, _, plot, species, _, _ in harvests
        ],
        candidates=[],
    )


async def _list_recent_activities(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
) -> ToolExecution:
    activities = await list_farm_activities(
        session,
        farm_id=farm_id,
        user_id=user_id,
        limit=TOOL_RESULT_LIMIT,
    )
    references: list[AIReference] = []
    records: list[dict[str, Any]] = []
    for activity in activities:
        records.append(
            {
                "type": activity.type,
                "occurred_at": _datetime(activity.occurred_at),
                "plot_id": activity.plot.id,
                "plot_name": activity.plot.name,
                "species": activity.species_name,
                "operation_type": activity.operation_type_name,
                "quantity": _number(activity.quantity),
                "unit": activity.unit,
            }
        )
        if activity.production_id:
            references.append(
                _production_reference(activity.production_id, activity.species_name or "种养", None)
            )
        elif activity.operation_id:
            references.append(
                AIReference(
                    kind="OPERATION",
                    id=activity.operation_id,
                    label=f"{activity.operation_type_name or '农事'} · {activity.plot.name}",
                    route=f"/pages/operations/detail?operationId={activity.operation_id}",
                )
            )
        elif activity.harvest_id:
            references.append(
                AIReference(
                    kind="HARVEST",
                    id=activity.harvest_id,
                    label=f"{activity.species_name or '收获'} · {activity.plot.name}",
                    route=f"/pages/harvests/detail?harvestId={activity.harvest_id}",
                )
            )
    return ToolExecution(data={"activities": records}, references=references, candidates=[])


async def _list_species(session: AsyncSession, *, keyword: str | None) -> ToolExecution:
    species, _ = await list_species(
        session,
        industry=None,
        keyword=keyword,
        page=1,
        page_size=TOOL_RESULT_LIMIT,
    )
    references = [
        AIReference(kind="SPECIES", id=item.id, label=item.name, route="/pages/species/index")
        for item in species
    ]
    return ToolExecution(
        data={
            "species": [
                {
                    "id": item.id,
                    "name": item.name,
                    "industry": item.industry,
                    "individual_unit": item.individual_unit,
                }
                for item in species
            ]
        },
        references=references,
        candidates=references if keyword is not None and len(references) > 1 else [],
    )


async def _list_operation_types(session: AsyncSession) -> ToolExecution:
    operation_types, _ = await list_operation_types(
        session,
        page=1,
        page_size=TOOL_RESULT_LIMIT,
    )
    return ToolExecution(
        data={
            "operation_types": [
                {"id": item.id, "name": item.name, "code": item.code} for item in operation_types
            ]
        },
        references=[],
        candidates=[],
    )


def _plot_reference(plot_id: int, name: str) -> AIReference:
    return AIReference(
        kind="PLOT",
        id=plot_id,
        label=name,
        route=f"/pages/plots/detail?plotId={plot_id}",
    )


def _production_reference(
    production_id: int,
    species_name: str,
    variety: str | None,
) -> AIReference:
    label = species_name if not variety else f"{species_name} · {variety}"
    return AIReference(
        kind="PRODUCTION",
        id=production_id,
        label=label,
        route=f"/pages/productions/detail?productionId={production_id}",
    )


def _number(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _datetime(value) -> str:
    return value.replace(tzinfo=UTC).isoformat()
