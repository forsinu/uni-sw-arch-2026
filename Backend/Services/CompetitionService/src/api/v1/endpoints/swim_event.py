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
    swimEventRepositoryHandler,
    swimMeetingRepositoryHandler,
)
from src.db.errors import DbConflictError
from src.db.models.swim_event import RaceDistance, RaceGender, RaceStroke
from src.db.repositories import SwimEventRepository, SwimMeetingRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swim_event import (
    PaginatedSwimEventResp,
    SwimEventCreateReq,
    SwimEventResp,
    SwimEventUpdateReq,
)


router = APIRouter(
    tags=["Swim Events"],
)


@router.get(
    "/meetings/{meetingId}/events",
    response_model=PaginatedSwimEventResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimEventsByMeeting",
)
async def listSwimEventsByMeeting(
    meetingId: uuid.UUID,
    # access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
    stroke: Annotated[RaceStroke | None, Query()] = None,
    gender: Annotated[RaceGender | None, Query()] = None,
    distance: Annotated[RaceDistance | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, events = await eventRepository.listEventsByMeetingId(
        meetingId=meetingId,
        stroke=stroke,
        gender=gender,
        distance=distance,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimEventResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": events,
        }
    )


@router.post(
    "/meetings/{meetingId}/events",
    response_model=SwimEventResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSwimEvent",
)
async def createSwimEvent(
    meetingId: uuid.UUID,
    payload: SwimEventCreateReq,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
):
    try:
        async with database.transaction(session):
            meeting = await meetingRepository.getMeetingById(meetingId)

            if meeting is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Swim meeting not found.",
                )

            event = await eventRepository.createEvent(
                meetingId=meetingId,
                distance=payload.distance,
                stroke=payload.stroke,
                gender=payload.gender,
                startAt=payload.startAt,
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This swim event already exists for the selected meeting.",
        ) from exc

    return event


@router.get(
    "/events/{eventId}",
    response_model=SwimEventResp,
    status_code=status.HTTP_200_OK,
    operation_id="getSwimEvent",
)
async def getSwimEvent(
    eventId: uuid.UUID,
    # access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
):
    event = await eventRepository.getEventById(eventId)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim event not found.",
        )

    return event


@router.patch(
    "/events/{eventId}",
    response_model=SwimEventResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimEvent",
)
async def updateSwimEvent(
    eventId: uuid.UUID,
    payload: SwimEventUpdateReq,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
):
    async with database.transaction(session):
        event = await eventRepository.getEventById(eventId)

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim event not found.",
            )

        event = await eventRepository.updateEvent(
            event=event,
            distance=payload.distance,
            stroke=payload.stroke,
            gender=payload.gender,
            startAt=payload.startAt,
        )

    return event


@router.delete(
    "/events/{eventId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deleteSwimEvent",
)
async def deleteSwimEvent(
    eventId: uuid.UUID,
    access: Annotated[AccessContext, Depends(adminAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
):
    async with database.transaction(session):
        event = await eventRepository.getEventById(eventId)

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim event not found.",
            )

        await eventRepository.deleteEvent(event)

    return {"msg": "Swim event deleted successfully."}
