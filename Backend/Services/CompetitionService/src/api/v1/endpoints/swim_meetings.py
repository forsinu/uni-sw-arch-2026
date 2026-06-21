from datetime import date
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    AccessContext,
    adminAccessHandler,
    authenticatedAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    swimMeetingRepositoryHandler,
)
from src.db.errors import DbConflictError
from src.db.models.swim_meeting import SwimMeetingStatus
from src.db.repositories import SwimMeetingRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swim_meeting import (
    PaginatedSwimMeetingResp,
    SwimMeetingCreateReq,
    SwimMeetingResp,
    SwimMeetingStatusUpdateReq,
    SwimMeetingUpdateReq,
)


router = APIRouter(
    prefix="/meetings",
    tags=["Swim Meetings"],
)


@router.get(
    "",
    response_model=PaginatedSwimMeetingResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimMeetings",
)
async def listSwimMeetings(
    # access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    meetingStatus: Annotated[SwimMeetingStatus | None, Query(alias="status")] = None,
    organizerTeamId: Annotated[uuid.UUID | None, Query()] = None,
    swimmingPoolId: Annotated[uuid.UUID | None, Query()] = None,
    dateFrom: Annotated[date | None, Query()] = None,
    dateTo: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, meetings = await meetingRepository.listMeetings(
        status=meetingStatus,
        organizerTeamId=organizerTeamId,
        swimmingPoolId=swimmingPoolId,
        dateFrom=dateFrom,
        dateTo=dateTo,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimMeetingResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": meetings,
        }
    )


@router.post(
    "",
    response_model=SwimMeetingResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSwimMeeting",
)
async def createSwimMeeting(
    payload: SwimMeetingCreateReq,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
):
    try:
        async with database.transaction(session):
            meeting = await meetingRepository.createMeeting(
                name=payload.name,
                poolLength=payload.poolLength,
                entriesOpenAt=payload.entriesOpenAt,
                entriesCloseAt=payload.entriesCloseAt,
                startDate=payload.startDate,
                endDate=payload.endDate,
                organizerTeamId=payload.organizerTeamId,
                swimmingPoolId=payload.swimmingPoolId,
                status=payload.status,
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A swim meeting with the same name and start date already exists.",
        ) from exc

    return meeting


@router.get(
    "/{meetingId}",
    response_model=SwimMeetingResp,
    status_code=status.HTTP_200_OK,
    operation_id="getSwimMeeting",
)
async def getSwimMeeting(
    meetingId: uuid.UUID,
    # access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
):
    meeting = await meetingRepository.getMeetingById(meetingId)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim meeting not found.",
        )

    return meeting


@router.patch(
    "/{meetingId}",
    response_model=SwimMeetingResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimMeeting",
)
async def updateSwimMeeting(
    meetingId: uuid.UUID,
    payload: SwimMeetingUpdateReq,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
):
    async with database.transaction(session):
        meeting = await meetingRepository.getMeetingById(meetingId)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim meeting not found.",
            )

        meeting = await meetingRepository.updateMeeting(
            meeting=meeting,
            name=payload.name,
            poolLength=payload.poolLength,
            entriesOpenAt=payload.entriesOpenAt,
            entriesCloseAt=payload.entriesCloseAt,
            startDate=payload.startDate,
            endDate=payload.endDate,
            organizerTeamId=payload.organizerTeamId,
            swimmingPoolId=payload.swimmingPoolId,
            status=payload.status,
        )

    return meeting


@router.patch(
    "/{meetingId}/status",
    response_model=SwimMeetingResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimMeetingStatus",
)
async def updateSwimMeetingStatus(
    meetingId: uuid.UUID,
    payload: SwimMeetingStatusUpdateReq,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
):
    async with database.transaction(session):
        meeting = await meetingRepository.getMeetingById(meetingId)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim meeting not found.",
            )

        meeting = await meetingRepository.updateMeetingStatus(
            meeting=meeting,
            status=payload.status,
        )

    return meeting


@router.delete(
    "/{meetingId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deleteSwimMeeting",
)
async def deleteSwimMeeting(
    meetingId: uuid.UUID,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
):
    async with database.transaction(session):
        meeting = await meetingRepository.getMeetingById(meetingId)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim meeting not found.",
            )

        await meetingRepository.deleteMeeting(meeting)

    return {"msg": "Swim meeting deleted successfully."}


@router.patch(
    "/{meetingId}/referee",
    response_model=SwimMeetingResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimMeetingReferee",
)
async def addRefereeToMeeting(
    meetingId: uuid.UUID,
    payload: SwimMeetingStatusUpdateReq,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
):
    async with database.transaction(session):
        meeting = await meetingRepository.getMeetingById(meetingId)

        if meeting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim meeting not found.",
            )

        meeting = await meetingRepository.updateMeetingStatus(
            meeting=meeting,
            status=payload.status,
        )

    return meeting
