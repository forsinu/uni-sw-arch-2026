# src/api/v1/endpoints/referee.py

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    adminOrRefereeAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    swimMeetingRepositoryHandler,
    swimMeetingRefereeRepositoryHandler,
)
from src.core.security.models import AccessTokenPayload
from src.db.errors import DbConflictError
from src.db.repositories.swim_meeting import SwimMeetingRepository
from src.db.repositories.swim_meeting_referee import SwimMeetingRefereeRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swim_meeting_referee import (
    PaginatedSwimMeetingRefereeResp,
    SwimMeetingRefereeAddReq,
    SwimMeetingRefereeRemoveReq,
)


router = APIRouter(
    prefix="/referees",
    tags=["Swim Meeting Referees"],
)


def _getRoleValue(accessToken: AccessTokenPayload) -> str:
    role = getattr(accessToken, "role", None)

    if role is None:
        return ""

    if hasattr(role, "value"):
        return str(role.value)

    return str(role)


def _isAdmin(accessToken: AccessTokenPayload) -> bool:
    return _getRoleValue(accessToken) == "ADMIN"


def _getRefereeFederationIdFromToken(
    accessToken: AccessTokenPayload,
) -> str:
    if accessToken.fed is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The current user is not associated with a referee federation id.",
        )

    return str(accessToken.fed)


def _ensureCanUseRefereeFederationId(
    accessToken: AccessTokenPayload,
    refereeFederationId: str,
) -> None:
    if _isAdmin(accessToken):
        return

    tokenRefereeFederationId = _getRefereeFederationIdFromToken(accessToken)

    if refereeFederationId != tokenRefereeFederationId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Referees can only operate on their own referee federation id.",
        )


async def requireRefereeAssignedToMeeting(
    meetingId: uuid.UUID,
    accessToken: AccessTokenPayload,
    refereeRepository: SwimMeetingRefereeRepository,
) -> None:
    refereeFederationId = _getRefereeFederationIdFromToken(accessToken)

    isAssigned = await refereeRepository.isRefereeAssignedToMeeting(
        meetingId=meetingId,
        refereeFederationId=refereeFederationId,
    )

    if not isAssigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only referees assigned to this swim meeting can perform this operation.",
        )


@router.post(
    "",
    response_model=MessageResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="addRefereeToSwimMeeting",
)
async def addRefereeToSwimMeeting(
    payload: SwimMeetingRefereeAddReq,
    accessToken: Annotated[AccessTokenPayload, Depends(adminOrRefereeAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    refereeRepository: Annotated[
        SwimMeetingRefereeRepository,
        Depends(swimMeetingRefereeRepositoryHandler),
    ],
):
    _ensureCanUseRefereeFederationId(
        accessToken=accessToken,
        refereeFederationId=payload.refereeFederationId,
    )

    meeting = await meetingRepository.getMeetingById(payload.meetingId)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim meeting not found.",
        )

    try:
        async with database.transaction(session):
            await refereeRepository.addRefereeToMeeting(
                meetingId=payload.meetingId,
                refereeFederationId=payload.refereeFederationId,
                assignedBy=accessToken.sub,
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This referee is already assigned to this swim meeting.",
        ) from exc

    return {"msg": "Referee assigned to swim meeting successfully."}


@router.delete(
    "",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="removeRefereeFromSwimMeeting",
)
async def removeRefereeFromSwimMeeting(
    payload: SwimMeetingRefereeRemoveReq,
    accessToken: Annotated[AccessTokenPayload, Depends(adminOrRefereeAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    refereeRepository: Annotated[
        SwimMeetingRefereeRepository,
        Depends(swimMeetingRefereeRepositoryHandler),
    ],
):
    _ensureCanUseRefereeFederationId(
        accessToken=accessToken,
        refereeFederationId=payload.refereeFederationId,
    )

    meeting = await meetingRepository.getMeetingById(payload.meetingId)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim meeting not found.",
        )

    async with database.transaction(session):
        removed = await refereeRepository.removeRefereeFromMeeting(
            meetingId=payload.meetingId,
            refereeFederationId=payload.refereeFederationId,
        )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referee is not assigned to this swim meeting.",
        )

    return {"msg": "Referee removed from swim meeting successfully."}


@router.get(
    "/meetings/{meetingId}",
    response_model=PaginatedSwimMeetingRefereeResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimMeetingReferees",
)
async def listSwimMeetingReferees(
    meetingId: uuid.UUID,
    _: Annotated[AccessTokenPayload, Depends(adminOrRefereeAccessHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    refereeRepository: Annotated[
        SwimMeetingRefereeRepository,
        Depends(swimMeetingRefereeRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    meeting = await meetingRepository.getMeetingById(meetingId)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim meeting not found.",
        )

    totalRecords, referees = await refereeRepository.listMeetingReferees(
        meetingId=meetingId,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimMeetingRefereeResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": referees,
        }
    )


@router.get(
    "/me/meetings",
    response_model=PaginatedSwimMeetingRefereeResp,
    status_code=status.HTTP_200_OK,
    operation_id="listCurrentRefereeMeetings",
)
async def listCurrentRefereeMeetings(
    accessToken: Annotated[AccessTokenPayload, Depends(adminOrRefereeAccessHandler)],
    refereeRepository: Annotated[
        SwimMeetingRefereeRepository,
        Depends(swimMeetingRefereeRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    refereeFederationId = _getRefereeFederationIdFromToken(accessToken)

    totalRecords, refereeMeetings = await refereeRepository.listRefereeMeetings(
        refereeFederationId=refereeFederationId,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimMeetingRefereeResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": refereeMeetings,
        }
    )


@router.get(
    "/meetings/{meetingId}/me",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="checkCurrentRefereeAssignedToMeeting",
)
async def checkCurrentRefereeAssignedToMeeting(
    meetingId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(adminOrRefereeAccessHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    refereeRepository: Annotated[
        SwimMeetingRefereeRepository,
        Depends(swimMeetingRefereeRepositoryHandler),
    ],
):
    meeting = await meetingRepository.getMeetingById(meetingId)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim meeting not found.",
        )

    await requireRefereeAssignedToMeeting(
        meetingId=meetingId,
        accessToken=accessToken,
        refereeRepository=refereeRepository,
    )

    return {"msg": "Current referee is assigned to this swim meeting."}
