import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import AccessHandler, dbHandler, secHandler
from src.core.security import AccessTokenPayload, SecurityHandler
from src.core.util import getOneOr404, handleDbOp
from src.db.models.federation_members import (
    FederationMember,
    FederationRole,
)
from src.db.models.swimming_team import SwimmingTeam
from src.schema.member import (
    FederationMemberCreate,
    FederationMemberPatch,
    FederationMemberReq,
    PaginatedFederationMemberReq,
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


def validateMemberBusinessRules(
    fedRole: FederationRole,
    teamId: uuid.UUID | None,
    birth,
) -> None:
    if fedRole == FederationRole.ATHLETE and birth is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="birth is required for athletes",
        )

    if fedRole != FederationRole.REFEREE and teamId is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="teamId is required for non-referee members",
        )


@router.post(
    "",
    response_model=FederationMemberReq,
    status_code=status.HTTP_201_CREATED,
)
async def createFederationMember(
    payload: FederationMemberCreate,
    db: DbSessionDep,
    sec: SecSessionDep,
    _: AdminUserDep,
) -> FederationMember:
    validateMemberBusinessRules(
        fedRole=payload.fedRole,
        teamId=payload.teamId,
        birth=payload.birth,
    )

    if payload.fedRole != FederationRole.REFEREE and payload.teamId is not None:
        await getOneOr404(
            db,
            SwimmingTeam,
            SwimmingTeam.id == payload.teamId,
            errorMsg="Could not retrieve team.",
            notFoundMsg="Team not found",
        )

    for _ in range(10):
        memberCode = sec.generateMemberCode()

        federationId = FederationMember.buildFederationId(
            role=payload.fedRole,
            teamId=payload.teamId,
            memberCode=memberCode,
        )

        member = FederationMember(
            federationId=federationId,
            fedRole=payload.fedRole,
            teamId=payload.teamId,
            birth=payload.birth,
            memberCode=memberCode,
            firstName=payload.firstName,
            lastName=payload.lastName,
            isActive=payload.isActive,
        )

        db.add(member)

        try:
            await db.commit()
            await db.refresh(member)
            return member

        except IntegrityError:
            await db.rollback()

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Could not generate a unique federation member code",
    )


@router.get(
    "",
    response_model=PaginatedFederationMemberReq,
)
async def listFederationMembers(
    db: DbSessionDep,
    teamId: uuid.UUID | None = Query(default=None),
    fedRole: FederationRole | None = Query(default=None),
    isActive: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedFederationMemberReq:
    baseStmt = select(FederationMember)

    if teamId is not None:
        baseStmt = baseStmt.where(FederationMember.teamId == teamId)

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
        errorMsg="Could not list federation members.",
    ):
        totalResult = await db.execute(totalStmt)
        totalRecords = totalResult.scalar_one()

        dataResult = await db.execute(dataStmt)
        members = list(dataResult.scalars().all())

    return PaginatedFederationMemberReq.model_validate(
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


@router.get(
    "/federation/{federationId}",
    response_model=FederationMemberReq,
)
async def getFederationMemberByFederationId(
    federationId: str,
    db: DbSessionDep,
) -> FederationMember:
    return await getOneOr404(
        db,
        FederationMember,
        FederationMember.federationId == federationId,
        errorMsg="Could not retrieve federation member.",
        notFoundMsg="Federation member not found",
    )


@router.get(
    "/{memberId}",
    response_model=FederationMemberReq,
)
async def getFederationMember(
    memberId: uuid.UUID,
    db: DbSessionDep,
) -> FederationMember:
    return await getOneOr404(
        db,
        FederationMember,
        FederationMember.id == memberId,
        errorMsg="Could not retrieve federation member.",
        notFoundMsg="Federation member not found",
    )


@router.patch(
    "/{memberId}",
    response_model=FederationMemberReq,
)
async def patchFederationMember(
    memberId: uuid.UUID,
    payload: FederationMemberPatch,
    db: DbSessionDep,
    _: AdminUserDep,
) -> FederationMember:
    member = await getOneOr404(
        db,
        FederationMember,
        FederationMember.id == memberId,
        errorMsg="Could not retrieve federation member.",
        notFoundMsg="Federation member not found",
    )

    updateData = payload.model_dump(exclude_unset=True)

    nextFedRole = updateData.get("fedRole", member.fedRole)
    nextTeamId = updateData.get("teamId", member.teamId)
    nextBirth = updateData.get("birth", member.birth)

    validateMemberBusinessRules(
        fedRole=nextFedRole,
        teamId=nextTeamId,
        birth=nextBirth,
    )

    if nextFedRole != FederationRole.REFEREE and nextTeamId is not None:
        await getOneOr404(
            db,
            SwimmingTeam,
            SwimmingTeam.id == nextTeamId,
            errorMsg="Could not retrieve team.",
            notFoundMsg="Team not found",
        )

    federationIdMustChange = (
        nextFedRole != member.fedRole or nextTeamId != member.teamId
    )

    for fieldName, fieldValue in updateData.items():
        setattr(member, fieldName, fieldValue)

    if federationIdMustChange:
        member.federationId = FederationMember.buildFederationId(
            role=nextFedRole,
            teamId=nextTeamId,
            memberCode=member.memberCode,
        )

    async with handleDbOp(
        session=db,
        errorMsg="Could not update federation member.",
        integrityMsg="Federation member update violates a unique constraint.",
    ):
        await db.commit()
        await db.refresh(member)

    return member
