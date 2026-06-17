from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    adminAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    federationMemberRepositoryHandler,
    secHandler,
    swimmingTeamRepositoryHandler,
)
from src.core.sec import SecurityHandler
from src.db.errors import DbConflictError
from src.db.models.federation_members import FederationRole
from src.db.repositories.federation_member import FederationMemberRepository
from src.db.repositories.swimming_team import SwimmingTeamRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.federation_member import (
    FederationMemberCreateReq,
    FederationMemberResp,
    FederationMemberUpdateReq,
    PaginatedFederationMemberResp,
)


router = APIRouter(
    prefix="/members",
    tags=["Federation Members"],
)


@router.get(
    "",
    response_model=PaginatedFederationMemberResp,
    status_code=status.HTTP_200_OK,
    operation_id="listFederationMembers",
)
async def listFederationMembers(
    _: Annotated[object, Depends(adminAccessHandler)],
    memberRepository: Annotated[
        FederationMemberRepository,
        Depends(federationMemberRepositoryHandler),
    ],
    teamId: Annotated[uuid.UUID | None, Query()] = None,
    fedRole: Annotated[FederationRole | None, Query()] = None,
    includeInactive: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, members = await memberRepository.listMembers(
        teamId=teamId,
        fedRole=fedRole,
        includeInactive=includeInactive,
        limit=limit,
        offset=offset,
    )

    return PaginatedFederationMemberResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": members,
        }
    )


@router.post(
    "",
    response_model=FederationMemberResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="createFederationMember",
)
async def createFederationMember(
    payload: FederationMemberCreateReq,
    _: Annotated[object, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    security: Annotated[SecurityHandler, Depends(secHandler)],
    memberRepository: Annotated[
        FederationMemberRepository,
        Depends(federationMemberRepositoryHandler),
    ],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    if payload.fedRole != FederationRole.REFEREE and payload.teamId is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="teamId is required for athletes, coaches, and team managers.",
        )

    async with database.transaction(session):
        if payload.teamId is not None:
            team = await teamRepository.getTeamById(
                teamId=payload.teamId,
                active=True,
            )

            if team is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target swimming team not found or inactive.",
                )

        memberCode = payload.memberCode or security.generateMemberCode()

        try:
            member = await memberRepository.createMember(
                fedRole=payload.fedRole,
                teamId=payload.teamId,
                memberCode=memberCode,
                firstName=payload.firstName,
                lastName=payload.lastName,
                birth=payload.birth,
            )

        except DbConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A federation member with the same identity already exists.",
            ) from exc

    return member


@router.get(
    "/{memberId}",
    response_model=FederationMemberResp,
    status_code=status.HTTP_200_OK,
    operation_id="getFederationMember",
)
async def getFederationMember(
    memberId: uuid.UUID,
    _: Annotated[object, Depends(adminAccessHandler)],
    memberRepository: Annotated[
        FederationMemberRepository,
        Depends(federationMemberRepositoryHandler),
    ],
):
    member = await memberRepository.getMemberById(memberId)

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Federation member not found.",
        )

    return member


@router.patch(
    "/{memberId}",
    response_model=FederationMemberResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateFederationMember",
)
async def updateFederationMember(
    memberId: uuid.UUID,
    payload: FederationMemberUpdateReq,
    _: Annotated[object, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    memberRepository: Annotated[
        FederationMemberRepository,
        Depends(federationMemberRepositoryHandler),
    ],
    teamRepository: Annotated[
        SwimmingTeamRepository,
        Depends(swimmingTeamRepositoryHandler),
    ],
):
    async with database.transaction(session):
        member = await memberRepository.getMemberById(memberId)

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Federation member not found.",
            )

        if payload.teamId is not None:
            team = await teamRepository.getTeamById(
                teamId=payload.teamId,
                active=True,
            )

            if team is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target swimming team not found or inactive.",
                )

        if (
            payload.firstName is not None
            or payload.lastName is not None
            or payload.birth is not None
        ):
            await memberRepository.updateMemberPersonalInfo(
                member=member,
                firstName=payload.firstName,
                lastName=payload.lastName,
                birth=payload.birth,
            )

        if payload.fedRole is not None or payload.teamId is not None:
            newRole = payload.fedRole or member.fedRole
            newTeamId = payload.teamId if payload.teamId is not None else member.teamId

            if newRole != FederationRole.REFEREE and newTeamId is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="teamId is required for non-referee federation members.",
                )

            await memberRepository.updateMemberRoleAndTeam(
                member=member,
                fedRole=newRole,
                teamId=newTeamId,
            )

        if payload.isActive is not None:
            await memberRepository.setMemberActiveStatus(
                member=member,
                isActive=payload.isActive,
            )

    return member


@router.delete(
    "/{memberId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deactivateFederationMember",
)
async def deactivateFederationMember(
    memberId: uuid.UUID,
    _: Annotated[object, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    memberRepository: Annotated[
        FederationMemberRepository,
        Depends(federationMemberRepositoryHandler),
    ],
):
    async with database.transaction(session):
        member = await memberRepository.getMemberById(memberId)

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Federation member not found.",
            )

        await memberRepository.deactivateMember(member)

    return {"msg": "Federation member deactivated successfully."}
