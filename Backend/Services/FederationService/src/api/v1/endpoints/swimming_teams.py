from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    adminAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    swimmingTeamRepositoryHandler,
)
from src.db.errors import DbConflictError
from src.db.repositories.swimming_team import SwimmingTeamRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swimming_team import (
    PaginatedSwimmingTeamResp,
    SwimmingTeamCreateReq,
    SwimmingTeamResp,
    SwimmingTeamUpdateReq,
)


router = APIRouter(
    prefix="/teams",
    tags=["Swimming Teams"],
)


@router.get(
    "",
    response_model=PaginatedSwimmingTeamResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimmingTeams",
)
async def listSwimmingTeams(
    # _: Annotated[object, Depends(adminAccessHandler)],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
    includeInactive: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, teams = await teamRepository.listTeams(
        includeInactive=includeInactive,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimmingTeamResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": teams,
        }
    )


@router.post(
    "",
    response_model=SwimmingTeamResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSwimmingTeam",
)
async def createSwimmingTeam(
    payload: SwimmingTeamCreateReq,
    _: Annotated[object, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    try:
        async with database.transaction(session):
            team = await teamRepository.createTeam(
                name=payload.name,
                shortName=payload.shortName,
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team with the same name or short name already exists.",
        ) from exc

    return team


@router.get(
    "/{teamId}",
    response_model=SwimmingTeamResp,
    status_code=status.HTTP_200_OK,
    operation_id="getSwimmingTeam",
)
async def getSwimmingTeam(
    teamId: uuid.UUID,
    # _: Annotated[object, Depends(adminAccessHandler)],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    team = await teamRepository.getTeamById(teamId)

    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swimming team not found.",
        )

    return team


@router.patch(
    "/{teamId}",
    response_model=SwimmingTeamResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimmingTeam",
)
async def updateSwimmingTeam(
    teamId: uuid.UUID,
    payload: SwimmingTeamUpdateReq,
    _: Annotated[object, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    async with database.transaction(session):
        team = await teamRepository.getTeamById(teamId)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swimming team not found.",
            )

        team = await teamRepository.updateTeamInfo(
            team=team,
            name=payload.name,
            shortName=payload.shortName,
            isActive=payload.isActive,
        )

    return team


@router.delete(
    "/{teamId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deactivateSwimmingTeam",
)
async def deactivateSwimmingTeam(
    teamId: uuid.UUID,
    _: Annotated[object, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    async with database.transaction(session):
        team = await teamRepository.getTeamById(teamId)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swimming team not found.",
            )

        await teamRepository.updateTeamInfo(
            team=team,
            isActive=False,
        )

    return {"msg": "Swimming team deactivated successfully."}
