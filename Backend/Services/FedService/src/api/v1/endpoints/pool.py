import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import AccessHandler, dbHandler
from src.core.security import AccessTokenPayload
from src.core.util import getOneOr404, handleDbOp
from src.db.models.swimming_pool import PoolLength, SwimmingPool
from src.db.models.swimming_team import SwimmingTeam
from src.schema.pool import (
    PaginatedSwimmingPoolReq,
    SwimmingPoolCreate,
    SwimmingPoolPatch,
    SwimmingPoolReq,
)


router = APIRouter()

DbSessionDep = Annotated[AsyncSession, Depends(dbHandler)]

AuthenticatedUserDep = Annotated[
    AccessTokenPayload,
    Depends(AccessHandler()),
]

AdminUserDep = Annotated[
    AccessTokenPayload,
    Depends(AccessHandler(checkAdmin=True)),
]


async def validateTeamExistsIfProvided(
    db: AsyncSession,
    teamId: uuid.UUID | None,
) -> None:
    if teamId is None:
        return

    await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )


@router.post(
    "",
    response_model=SwimmingPoolReq,
    status_code=status.HTTP_201_CREATED,
)
async def createSwimmingPool(
    payload: SwimmingPoolCreate,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingPool:
    await validateTeamExistsIfProvided(db, payload.teamId)

    pool = SwimmingPool(**payload.model_dump())
    db.add(pool)

    async with handleDbOp(
        session=db,
        errorMsg="Could not create swimming pool.",
        integrityMsg="A swimming pool with the same name already exists or references an invalid team.",
    ):
        await db.commit()
        await db.refresh(pool)

    return pool


@router.get(
    "",
    response_model=PaginatedSwimmingPoolReq,
)
async def listSwimmingPools(
    db: DbSessionDep,
    _: AuthenticatedUserDep,
    teamId: uuid.UUID | None = Query(default=None),
    city: str | None = Query(default=None, min_length=1),
    countryIso: str | None = Query(default=None, min_length=2, max_length=2),
    lenPool: PoolLength | None = Query(default=None),
    unassignedOnly: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedSwimmingPoolReq:
    baseStmt = select(SwimmingPool)

    if teamId is not None:
        baseStmt = baseStmt.where(SwimmingPool.teamId == teamId)

    if unassignedOnly:
        baseStmt = baseStmt.where(SwimmingPool.teamId.is_(None))

    if city is not None:
        baseStmt = baseStmt.where(SwimmingPool.city.ilike(f"%{city}%"))

    if countryIso is not None:
        baseStmt = baseStmt.where(SwimmingPool.countryIso == countryIso.upper())

    if lenPool is not None:
        baseStmt = baseStmt.where(SwimmingPool.lenPool == lenPool)

    totalStmt = select(func.count()).select_from(baseStmt.subquery())
    dataStmt = (
        baseStmt.order_by(SwimmingPool.city, SwimmingPool.name)
        .limit(limit)
        .offset(offset)
    )

    async with handleDbOp(
        session=db,
        errorMsg="Could not list swimming pools.",
    ):
        totalResult = await db.execute(totalStmt)
        totalRecords = totalResult.scalar_one()

        dataResult = await db.execute(dataStmt)
        pools = list(dataResult.scalars().all())

    return PaginatedSwimmingPoolReq.model_validate(
        {
            "pools": pools,
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": offset + limit < totalRecords,
            },
        }
    )


@router.get(
    "/{poolId}",
    response_model=SwimmingPoolReq,
)
async def getSwimmingPool(
    poolId: uuid.UUID,
    db: DbSessionDep,
    _: AuthenticatedUserDep,
) -> SwimmingPool:
    return await getOneOr404(
        db,
        SwimmingPool,
        SwimmingPool.id == poolId,
        errorMsg="Could not retrieve swimming pool.",
        notFoundMsg="Swimming pool not found",
    )


@router.patch(
    "/{poolId}",
    response_model=SwimmingPoolReq,
)
async def patchSwimmingPool(
    poolId: uuid.UUID,
    payload: SwimmingPoolPatch,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingPool:
    pool = await getOneOr404(
        db,
        SwimmingPool,
        SwimmingPool.id == poolId,
        errorMsg="Could not retrieve swimming pool.",
        notFoundMsg="Swimming pool not found",
    )

    updateData = payload.model_dump(exclude_unset=True)

    if "teamId" in updateData:
        await validateTeamExistsIfProvided(db, updateData["teamId"])

    if "countryIso" in updateData and updateData["countryIso"] is not None:
        updateData["countryIso"] = updateData["countryIso"].upper()

    for fieldName, fieldValue in updateData.items():
        setattr(pool, fieldName, fieldValue)

    async with handleDbOp(
        session=db,
        errorMsg="Could not update swimming pool.",
        integrityMsg="Swimming pool update violates a unique constraint or references an invalid team.",
    ):
        await db.commit()
        await db.refresh(pool)

    return pool


@router.delete(
    "/{poolId}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deleteSwimmingPool(
    poolId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> None:
    pool = await getOneOr404(
        db,
        SwimmingPool,
        SwimmingPool.id == poolId,
        errorMsg="Could not retrieve swimming pool.",
        notFoundMsg="Swimming pool not found",
    )

    await db.delete(pool)

    async with handleDbOp(
        session=db,
        errorMsg="Could not delete swimming pool.",
        integrityMsg="Could not delete swimming pool because it is still referenced.",
    ):
        await db.commit()


@router.put(
    "/{poolId}/team/{teamId}",
    response_model=SwimmingPoolReq,
)
async def assignSwimmingPoolToTeam(
    poolId: uuid.UUID,
    teamId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingPool:
    await validateTeamExistsIfProvided(db, teamId)

    pool = await getOneOr404(
        db,
        SwimmingPool,
        SwimmingPool.id == poolId,
        errorMsg="Could not retrieve swimming pool.",
        notFoundMsg="Swimming pool not found",
    )

    pool.teamId = teamId

    async with handleDbOp(
        session=db,
        errorMsg="Could not assign swimming pool to team.",
        integrityMsg="Could not assign swimming pool to team because of a relation integrity error.",
    ):
        await db.commit()
        await db.refresh(pool)

    return pool


@router.delete(
    "/{poolId}/team",
    response_model=SwimmingPoolReq,
)
async def detachSwimmingPoolFromTeam(
    poolId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingPool:
    pool = await getOneOr404(
        db,
        SwimmingPool,
        SwimmingPool.id == poolId,
        errorMsg="Could not retrieve swimming pool.",
        notFoundMsg="Swimming pool not found",
    )

    pool.teamId = None

    async with handleDbOp(
        session=db,
        errorMsg="Could not detach swimming pool from team.",
    ):
        await db.commit()
        await db.refresh(pool)

    return pool
