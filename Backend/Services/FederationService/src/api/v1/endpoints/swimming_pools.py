from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    AccessContext,
    adminOrTeamManagerAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    swimmingPoolRepositoryHandler,
    swimmingTeamRepositoryHandler,
)
from src.db.errors import DbConflictError
from src.db.models.swimming_pool import SwimmingPool
from src.db.repositories.swimming_pool import SwimmingPoolRepository
from src.db.repositories.swimming_team import SwimmingTeamRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swimming_pool import (
    PaginatedSwimmingPoolResp,
    SwimmingPoolCreateReq,
    SwimmingPoolResp,
    SwimmingPoolUpdateReq,
)


router = APIRouter(
    prefix="/pools",
    tags=["Swimming Pools"],
)


def ensureCanManagePool(
    access: AccessContext,
    pool: SwimmingPool,
) -> None:
    if access.isAdmin:
        return

    if access.teamId is None or pool.teamId != access.teamId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can manage only swimming pools assigned to your own team.",
        )


@router.get(
    "",
    response_model=PaginatedSwimmingPoolResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimmingPools",
)
async def listSwimmingPools(
    # access: Annotated[AccessContext, Depends(adminOrTeamManagerAccessHandler)],
    poolRepository: Annotated[
        SwimmingPoolRepository,
        Depends(swimmingPoolRepositoryHandler),
    ],
    city: Annotated[str | None, Query(max_length=64)] = None,
    countryIso: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    teamId: Annotated[uuid.UUID | None, Query()] = None,
    includeInactive: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    effectiveTeamId = teamId

    # if not access.isAdmin:
    #     effectiveTeamId = access.teamId

    totalRecords, pools = await poolRepository.listPools(
        city=city,
        countryIso=countryIso,
        teamId=effectiveTeamId,
        includeInactive=includeInactive,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimmingPoolResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": pools,
        }
    )


@router.post(
    "",
    response_model=SwimmingPoolResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSwimmingPool",
)
async def createSwimmingPool(
    payload: SwimmingPoolCreateReq,
    access: Annotated[AccessContext, Depends(adminOrTeamManagerAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    poolRepository: Annotated[
        SwimmingPoolRepository,
        Depends(swimmingPoolRepositoryHandler),
    ],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    targetTeamId = payload.teamId

    if not access.isAdmin:
        targetTeamId = access.teamId

    async with database.transaction(session):
        if targetTeamId is not None:
            team = await teamRepository.getTeamById(
                teamId=targetTeamId,
                active=True,
            )

            if team is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target swimming team not found or inactive.",
                )

        try:
            pool = await poolRepository.createPool(
                name=payload.name,
                poolType=payload.poolType,
                poolLength=payload.poolLength,
                laneCount=payload.laneCount,
                streetAddress=payload.streetAddress,
                city=payload.city,
                postalCode=payload.postalCode,
                countryIso=payload.countryIso,
                teamId=targetTeamId,
            )

        except DbConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A swimming pool with the same identity already exists.",
            ) from exc

    return pool


@router.get(
    "/{poolId}",
    response_model=SwimmingPoolResp,
    status_code=status.HTTP_200_OK,
    operation_id="getSwimmingPool",
)
async def getSwimmingPool(
    poolId: uuid.UUID,
    # access: Annotated[AccessContext, Depends(adminOrTeamManagerAccessHandler)],
    poolRepository: Annotated[
        SwimmingPoolRepository,
        Depends(swimmingPoolRepositoryHandler),
    ],
):
    pool = await poolRepository.getPoolById(poolId)

    if pool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swimming pool not found.",
        )

    # ensureCanManagePool(access, pool)

    return pool


@router.patch(
    "/{poolId}",
    response_model=SwimmingPoolResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimmingPool",
)
async def updateSwimmingPool(
    poolId: uuid.UUID,
    payload: SwimmingPoolUpdateReq,
    access: Annotated[AccessContext, Depends(adminOrTeamManagerAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    poolRepository: Annotated[
        SwimmingPoolRepository,
        Depends(swimmingPoolRepositoryHandler),
    ],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    async with database.transaction(session):
        pool = await poolRepository.getPoolById(poolId)

        if pool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swimming pool not found.",
            )

        ensureCanManagePool(access, pool)

        targetTeamId = payload.teamId

        if not access.isAdmin:
            if payload.teamId is not None and payload.teamId != access.teamId:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Team managers cannot reassign pools to another team.",
                )

            targetTeamId = None

        if targetTeamId is not None:
            team = await teamRepository.getTeamById(
                teamId=targetTeamId,
                active=True,
            )

            if team is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target swimming team not found or inactive.",
                )

        pool = await poolRepository.updatePool(
            pool=pool,
            name=payload.name,
            poolType=payload.poolType,
            poolLength=payload.poolLength,
            laneCount=payload.laneCount,
            streetAddress=payload.streetAddress,
            city=payload.city,
            postalCode=payload.postalCode,
            countryIso=payload.countryIso,
            teamId=targetTeamId,
            isActive=payload.isActive,
        )

    return pool


@router.delete(
    "/{poolId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deactivateSwimmingPool",
)
async def deactivateSwimmingPool(
    poolId: uuid.UUID,
    access: Annotated[AccessContext, Depends(adminOrTeamManagerAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    poolRepository: Annotated[
        SwimmingPoolRepository,
        Depends(swimmingPoolRepositoryHandler),
    ],
):
    async with database.transaction(session):
        pool = await poolRepository.getPoolById(poolId)

        if pool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swimming pool not found.",
            )

        ensureCanManagePool(access, pool)

        await poolRepository.deactivatePool(pool)

    return {"msg": "Swimming pool deactivated successfully."}
