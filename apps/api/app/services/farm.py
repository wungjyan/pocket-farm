import secrets

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException
from app.models.farm import Farm, FarmMember, FarmMemberRole
from app.models.user import User

FARM_CODE_MIN = 100000
FARM_CODE_MAX = 999999
FARM_CODE_CREATE_RETRIES = 10


def generate_farm_code() -> str:
    return str(secrets.randbelow(FARM_CODE_MAX - FARM_CODE_MIN + 1) + FARM_CODE_MIN)


def _not_found(message: str) -> AppException:
    return AppException(status_code=404, code=ErrorCode.NOT_FOUND, message=message)


def _forbidden(message: str) -> AppException:
    return AppException(status_code=403, code=ErrorCode.FORBIDDEN, message=message)


def _conflict(message: str) -> AppException:
    return AppException(status_code=409, code=ErrorCode.BUSINESS_CONFLICT, message=message)


async def create_farm(
    session: AsyncSession,
    *,
    created_by: int,
    name: str,
    region: str | None,
) -> Farm:
    """Create a farm and its initial owner in one transaction."""
    for _ in range(FARM_CODE_CREATE_RETRIES):
        farm = Farm(farm_code=generate_farm_code(), name=name, region=region, created_by=created_by)
        session.add(farm)
        try:
            await session.flush()
            session.add(FarmMember(farm_id=farm.id, user_id=created_by, role=FarmMemberRole.OWNER))
            await session.flush()
            await session.commit()
            return farm
        except IntegrityError:
            await session.rollback()

    raise _conflict("Unable to generate a unique farm code.")


async def get_farm_with_member(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
) -> tuple[Farm, FarmMember]:
    result = await session.execute(
        select(Farm, FarmMember)
        .join(FarmMember, FarmMember.farm_id == Farm.id)
        .where(Farm.id == farm_id, FarmMember.user_id == user_id)
    )
    farm_and_member = result.one_or_none()
    if farm_and_member is None:
        raise _not_found("Farm not found.")
    return farm_and_member


async def _lock_farm_members(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
) -> tuple[Farm, FarmMember, list[FarmMember]]:
    farm_result = await session.execute(select(Farm).where(Farm.id == farm_id).with_for_update())
    farm = farm_result.scalar_one_or_none()
    if farm is None:
        raise _not_found("Farm not found.")

    members_result = await session.execute(
        select(FarmMember).where(FarmMember.farm_id == farm_id).with_for_update()
    )
    members = list(members_result.scalars())
    current_member = next((member for member in members if member.user_id == user_id), None)
    if current_member is None:
        raise _not_found("Farm not found.")
    return farm, current_member, members


def _require_member_management_role(member: FarmMember) -> None:
    if member.role not in (FarmMemberRole.OWNER, FarmMemberRole.ADMIN):
        raise _forbidden("You do not have permission to manage farm members.")


def _require_target_permission(
    actor: FarmMember,
    target: FarmMember,
    *,
    new_role: FarmMemberRole | None = None,
) -> None:
    if actor.user_id == target.user_id:
        raise _forbidden("Use the leave-farm endpoint to leave the farm.")
    if actor.role == FarmMemberRole.MEMBER:
        raise _forbidden("You do not have permission to manage farm members.")
    if actor.role == FarmMemberRole.ADMIN and (
        target.role == FarmMemberRole.OWNER or new_role == FarmMemberRole.OWNER
    ):
        raise _forbidden("ADMIN cannot operate on or create an OWNER.")


async def list_my_farms(
    session: AsyncSession,
    *,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[tuple[Farm, FarmMemberRole]], int]:
    total = await session.scalar(
        select(func.count()).select_from(FarmMember).where(FarmMember.user_id == user_id)
    )
    result = await session.execute(
        select(Farm, FarmMember.role)
        .join(FarmMember, FarmMember.farm_id == Farm.id)
        .where(FarmMember.user_id == user_id)
        .order_by(Farm.created_at.desc(), Farm.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    farms = [(farm, FarmMemberRole(role)) for farm, role in result.all()]
    return farms, int(total or 0)


async def resolve_current_farm(
    session: AsyncSession,
    *,
    user: User,
) -> tuple[Farm, FarmMemberRole] | None:
    """Return the user's valid preferred farm, or persist the list's first farm as fallback."""
    if user.preferred_farm_id is not None:
        preferred_result = await session.execute(
            select(Farm, FarmMember.role)
            .join(FarmMember, FarmMember.farm_id == Farm.id)
            .where(Farm.id == user.preferred_farm_id, FarmMember.user_id == user.id)
        )
        preferred = preferred_result.one_or_none()
        if preferred is not None:
            farm, role = preferred
            return farm, FarmMemberRole(role)

    fallback_result = await session.execute(
        select(Farm, FarmMember.role)
        .join(FarmMember, FarmMember.farm_id == Farm.id)
        .where(FarmMember.user_id == user.id)
        .order_by(Farm.created_at.desc(), Farm.id.desc())
        .limit(1)
    )
    fallback = fallback_result.one_or_none()
    fallback_farm_id = fallback[0].id if fallback is not None else None
    if user.preferred_farm_id != fallback_farm_id:
        user.preferred_farm_id = fallback_farm_id
        await session.commit()

    if fallback is None:
        return None
    farm, role = fallback
    return farm, FarmMemberRole(role)


async def set_current_farm(
    session: AsyncSession,
    *,
    user: User,
    farm_id: int,
) -> tuple[Farm, FarmMemberRole]:
    farm, member = await get_farm_with_member(session, farm_id=farm_id, user_id=user.id)
    user.preferred_farm_id = farm.id
    await session.commit()
    return farm, FarmMemberRole(member.role)


async def update_farm(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    name: str | None,
    region: str | None,
    ai_enabled: bool | None,
    fields_set: set[str],
) -> tuple[Farm, FarmMemberRole]:
    farm, member, _ = await _lock_farm_members(session, farm_id=farm_id, user_id=user_id)
    if member.role != FarmMemberRole.OWNER:
        raise _forbidden("Only an OWNER can edit farm information.")
    if "name" in fields_set:
        farm.name = name  # type: ignore[assignment]
    if "region" in fields_set:
        farm.region = region
    if "ai_enabled" in fields_set:
        farm.ai_enabled = ai_enabled  # type: ignore[assignment]
    await session.commit()
    await session.refresh(farm)
    return farm, FarmMemberRole(member.role)


async def list_members(
    session: AsyncSession,
    *,
    farm_id: int,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[tuple[FarmMember, User]], int]:
    await get_farm_with_member(session, farm_id=farm_id, user_id=user_id)
    total = await session.scalar(
        select(func.count()).select_from(FarmMember).where(FarmMember.farm_id == farm_id)
    )
    result = await session.execute(
        select(FarmMember, User)
        .join(User, User.id == FarmMember.user_id)
        .where(FarmMember.farm_id == farm_id)
        .order_by(FarmMember.joined_at.asc(), FarmMember.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.all()), int(total or 0)


async def add_member(
    session: AsyncSession,
    *,
    farm_id: int,
    actor_id: int,
    phone_number: str,
    role: FarmMemberRole,
) -> tuple[FarmMember, User]:
    _, actor, _ = await _lock_farm_members(session, farm_id=farm_id, user_id=actor_id)
    _require_member_management_role(actor)
    if actor.role == FarmMemberRole.ADMIN and role == FarmMemberRole.OWNER:
        raise _forbidden("ADMIN cannot create an OWNER.")

    result = await session.execute(select(User).where(User.phone_number == phone_number))
    user = result.scalar_one_or_none()
    if user is None:
        raise _not_found("Registered user not found.")

    member = FarmMember(farm_id=farm_id, user_id=user.id, role=role)
    session.add(member)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise _conflict("User is already a member of this farm.") from exc
    await session.refresh(member)
    return member, user


async def update_member_role(
    session: AsyncSession,
    *,
    farm_id: int,
    member_id: int,
    actor_id: int,
    role: FarmMemberRole,
) -> tuple[FarmMember, User]:
    _, actor, members = await _lock_farm_members(session, farm_id=farm_id, user_id=actor_id)
    target = next((member for member in members if member.id == member_id), None)
    if target is None:
        raise _not_found("Farm member not found.")
    _require_target_permission(actor, target, new_role=role)
    if target.role == FarmMemberRole.OWNER and role != FarmMemberRole.OWNER:
        if sum(member.role == FarmMemberRole.OWNER for member in members) <= 1:
            raise _conflict("A farm must always have at least one OWNER.")
    target.role = role
    await session.commit()
    user = await session.scalar(select(User).where(User.id == target.user_id))
    if user is None:
        raise _not_found("Registered user not found.")
    return target, user


async def remove_member(
    session: AsyncSession,
    *,
    farm_id: int,
    member_id: int,
    actor_id: int,
) -> None:
    _, actor, members = await _lock_farm_members(session, farm_id=farm_id, user_id=actor_id)
    target = next((member for member in members if member.id == member_id), None)
    if target is None:
        raise _not_found("Farm member not found.")
    _require_target_permission(actor, target)
    if (
        target.role == FarmMemberRole.OWNER
        and sum(member.role == FarmMemberRole.OWNER for member in members) <= 1
    ):
        raise _conflict("A farm must always have at least one OWNER.")
    await session.delete(target)
    await session.commit()


async def leave_farm(session: AsyncSession, *, farm_id: int, user_id: int) -> None:
    _, current_member, members = await _lock_farm_members(session, farm_id=farm_id, user_id=user_id)
    if (
        current_member.role == FarmMemberRole.OWNER
        and sum(member.role == FarmMemberRole.OWNER for member in members) <= 1
    ):
        raise _conflict("An OWNER cannot leave while they are the last OWNER.")
    await session.delete(current_member)
    await session.commit()
