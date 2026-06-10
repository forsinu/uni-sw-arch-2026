import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import AccessHandler, dbHandler, secHandler
from src.core.security import AccessTokenPayload, SecurityHandler
from src.core.util import getOneOr404, handleDbOp
from src.db.models.federation_members import FederationMember, FederationRole
from src.db.models.swimming_pool import SwimmingPool
from src.db.models.swimming_team import SwimmingTeam
from src.schema.team import (
    PaginatedSwimmingTeamReq,
    PaginatedTeamMemberReq,
    PaginatedTeamPoolReq,
    SwimmingTeamCreate,
    SwimmingTeamPatch,
    SwimmingTeamReq,
    TeamAthleteCreate,
    TeamMemberReq,
    TeamPoolReq,
)


router = APIRouter()

DbSessionDep = Annotated[AsyncSession, Depends(dbHandler)]
SecSessionDep = Annotated[SecurityHandler, Depends(secHandler)]

# AuthenticatedUserDep = Annotated[
#     AccessTokenPayload,
#     Depends(AccessHandler()),
# ]

AdminUserDep = Annotated[
    AccessTokenPayload,
    Depends(AccessHandler(checkAdmin=True)),
]


@router.post(
    "",
    response_model=SwimmingTeamReq,
    status_code=status.HTTP_201_CREATED,
)
async def createSwimmingTeam(
    payload: SwimmingTeamCreate,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingTeam:
    team = SwimmingTeam(**payload.model_dump())
    db.add(team)

    async with handleDbOp(
        session=db,
        errorMsg="Could not create swimming team.",
        integrityMsg="A swimming team with the same name, short name, or federation code already exists.",
    ):
        await db.commit()
        await db.refresh(team)

    return team


@router.get(
    "",
    response_model=PaginatedSwimmingTeamReq,
)
async def listSwimmingTeams(
    db: DbSessionDep,
    name: str | None = Query(default=None, min_length=1),
    isActive: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedSwimmingTeamReq:
    baseStmt = select(SwimmingTeam)

    if name is not None:
        baseStmt = baseStmt.where(SwimmingTeam.name.ilike(f"%{name}%"))

    if isActive is not None:
        baseStmt = baseStmt.where(SwimmingTeam.isActive == isActive)

    totalStmt = select(func.count()).select_from(baseStmt.subquery())
    dataStmt = baseStmt.order_by(SwimmingTeam.name).limit(limit).offset(offset)

    async with handleDbOp(
        session=db,
        errorMsg="Could not list swimming teams.",
    ):
        totalResult = await db.execute(totalStmt)
        totalRecords = totalResult.scalar_one()

        dataResult = await db.execute(dataStmt)
        teams = list(dataResult.scalars().all())

    return PaginatedSwimmingTeamReq.model_validate(
        {
            "teams": teams,
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": offset + limit < totalRecords,
            },
        }
    )


@router.get(
    "/{teamId}",
    response_model=SwimmingTeamReq,
)
async def getSwimmingTeam(
    teamId: uuid.UUID,
    db: DbSessionDep,
) -> SwimmingTeam:
    return await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )


@router.patch(
    "/{teamId}",
    response_model=SwimmingTeamReq,
)
async def patchSwimmingTeam(
    teamId: uuid.UUID,
    payload: SwimmingTeamPatch,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingTeam:
    team = await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )

    for fieldName, fieldValue in payload.model_dump(exclude_unset=True).items():
        setattr(team, fieldName, fieldValue)

    async with handleDbOp(
        session=db,
        errorMsg="Could not update swimming team.",
        integrityMsg="Swimming team update violates a unique constraint.",
    ):
        await db.commit()
        await db.refresh(team)

    return team


@router.delete(
    "/{teamId}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deleteSwimmingTeam(
    teamId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> None:
    team = await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )

    await db.delete(team)

    async with handleDbOp(
        session=db,
        errorMsg="Could not delete swimming team.",
        integrityMsg="Could not delete swimming team because it is still referenced.",
    ):
        await db.commit()


@router.get(
    "/{teamId}/members",
    response_model=PaginatedTeamMemberReq,
)
async def listTeamMembers(
    teamId: uuid.UUID,
    db: DbSessionDep,
    fedRole: FederationRole | None = Query(default=None),
    isActive: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedTeamMemberReq:
    await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )

    baseStmt = select(FederationMember).where(FederationMember.teamId == teamId)

    if fedRole is not None:
        baseStmt = baseStmt.where(FederationMember.fedRole == fedRole)

    if isActive is not None:
        baseStmt = baseStmt.where(FederationMember.isActive == isActive)

    totalStmt = select(func.count()).select_from(baseStmt.subquery())
    dataStmt = (
        baseStmt.order_by(FederationMember.lastName, FederationMember.firstName)
        .limit(limit)
        .offset(offset)
    )

    async with handleDbOp(
        session=db,
        errorMsg="Could not list team members.",
    ):
        totalResult = await db.execute(totalStmt)
        totalRecords = totalResult.scalar_one()

        dataResult = await db.execute(dataStmt)
        members = list(dataResult.scalars().all())

    return PaginatedTeamMemberReq.model_validate(
        {
            "members": members,
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": offset + limit < totalRecords,
            },
        }
    )


@router.post(
    "/{teamId}/athletes",
    response_model=TeamMemberReq,
    status_code=status.HTTP_201_CREATED,
)
async def createTeamAthlete(
    teamId: uuid.UUID,
    payload: TeamAthleteCreate,
    db: DbSessionDep,
    sec: SecSessionDep,
    _: AdminUserDep,
) -> FederationMember:
    await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )

    for _ in range(10):
        memberCode = sec.generateMemberCode()
        federationId = FederationMember.buildFederationId(
            role=FederationRole.ATHLETE,
            teamId=teamId,
            memberCode=memberCode,
        )

        athlete = FederationMember(
            federationId=federationId,
            fedRole=FederationRole.ATHLETE,
            teamId=teamId,
            birth=payload.birth,
            memberCode=memberCode,
            firstName=payload.firstName,
            lastName=payload.lastName,
            isActive=payload.isActive,
        )

        db.add(athlete)

        try:
            await db.commit()
            await db.refresh(athlete)
            return athlete
        except IntegrityError:
            await db.rollback()

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Could not generate a unique federation member code",
    )


@router.put(
    "/{teamId}/members/{memberId}",
    response_model=TeamMemberReq,
)
async def addExistingMemberToTeam(
    teamId: uuid.UUID,
    memberId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> FederationMember:
    await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )
    member = await getOneOr404(
        db,
        FederationMember,
        FederationMember.id == memberId,
        errorMsg="Could not retrieve federation member.",
        notFoundMsg="Federation member not found",
    )

    if member.fedRole == FederationRole.REFEREE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Referees cannot be assigned to a swimming team",
        )

    member.teamId = teamId
    member.federationId = FederationMember.buildFederationId(
        role=member.fedRole,
        teamId=teamId,
        memberCode=member.memberCode,
    )

    async with handleDbOp(
        session=db,
        errorMsg="Could not add member to swimming team.",
        integrityMsg="Could not add member to swimming team because of a unique constraint.",
    ):
        await db.commit()
        await db.refresh(member)

    return member


@router.delete(
    "/{teamId}/members/{memberId}",
    response_model=TeamMemberReq,
)
async def deactivateTeamMember(
    teamId: uuid.UUID,
    memberId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> FederationMember:
    member = await getOneOr404(
        db,
        FederationMember,
        FederationMember.id == memberId,
        FederationMember.teamId == teamId,
        errorMsg="Could not retrieve team member.",
        notFoundMsg="Team member not found",
    )
    member.isActive = False

    async with handleDbOp(
        session=db,
        errorMsg="Could not deactivate team member.",
    ):
        await db.commit()
        await db.refresh(member)

    return member


@router.get(
    "/{teamId}/pools",
    response_model=PaginatedTeamPoolReq,
)
async def listTeamPools(
    teamId: uuid.UUID,
    db: DbSessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedTeamPoolReq:
    await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )

    baseStmt = select(SwimmingPool).where(SwimmingPool.teamId == teamId)
    totalStmt = select(func.count()).select_from(baseStmt.subquery())
    dataStmt = baseStmt.order_by(SwimmingPool.name).limit(limit).offset(offset)

    async with handleDbOp(
        session=db,
        errorMsg="Could not list team swimming pools.",
    ):
        totalResult = await db.execute(totalStmt)
        totalRecords = totalResult.scalar_one()

        dataResult = await db.execute(dataStmt)
        pools = list(dataResult.scalars().all())

    return PaginatedTeamPoolReq.model_validate(
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


@router.put(
    "/{teamId}/pools/{poolId}",
    response_model=TeamPoolReq,
)
async def addSwimmingPoolToTeam(
    teamId: uuid.UUID,
    poolId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingPool:
    await getOneOr404(
        db,
        SwimmingTeam,
        SwimmingTeam.id == teamId,
        errorMsg="Could not retrieve swimming team.",
        notFoundMsg="Swimming team not found",
    )
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
        errorMsg="Could not add swimming pool to team.",
    ):
        await db.commit()
        await db.refresh(pool)

    return pool


@router.delete(
    "/{teamId}/pools/{poolId}",
    response_model=TeamPoolReq,
)
async def removeSwimmingPoolFromTeam(
    teamId: uuid.UUID,
    poolId: uuid.UUID,
    db: DbSessionDep,
    _: AdminUserDep,
) -> SwimmingPool:
    pool = await getOneOr404(
        db,
        SwimmingPool,
        SwimmingPool.id == poolId,
        SwimmingPool.teamId == teamId,
        errorMsg="Could not retrieve team swimming pool.",
        notFoundMsg="Team swimming pool not found",
    )
    pool.teamId = None

    async with handleDbOp(
        session=db,
        errorMsg="Could not remove swimming pool from team.",
    ):
        await db.commit()
        await db.refresh(pool)

    return pool
