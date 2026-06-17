from datetime import datetime
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    AccessContext,
    adminOrTeamManagerOrCoachAccessHandler,
    authenticatedAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    swimEventEntryRepositoryHandler,
    swimEventRepositoryHandler,
    swimMeetingRepositoryHandler,
)
from src.db.errors import DbConflictError
from src.db.models.swim_meeting import SwimMeetingStatus
from src.db.repositories import (
    SwimEventEntryRepository,
    SwimEventRepository,
    SwimMeetingRepository,
)
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swim_event_entry import (
    PaginatedSwimEventEntryResp,
    SwimEventEntryCreateReq,
    SwimEventEntryResp,
    SwimEventEntryUpdateReq,
)


router = APIRouter(
    tags=["Swim Event Entries"],
)


def getActorFederationId(access: AccessContext) -> str:
    if access.payload.fed:
        return access.payload.fed

    return str(access.payload.sub)


def ensureMeetingAcceptsEntries(
    meetingStatus: SwimMeetingStatus,
    entriesOpenAt: datetime,
    entriesCloseAt: datetime,
    nowUtc: datetime,
) -> None:
    if meetingStatus != SwimMeetingStatus.ENTRIES_OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entries are not open for this meeting.",
        )

    if nowUtc < entriesOpenAt or nowUtc > entriesCloseAt:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current time is outside the entry registration window.",
        )


@router.get(
    "/events/{eventId}/entries",
    response_model=PaginatedSwimEventEntryResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimEventEntries",
)
async def listSwimEventEntries(
    eventId: uuid.UUID,
    access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    entryRepository: Annotated[
        SwimEventEntryRepository,
        Depends(swimEventEntryRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, entries = await entryRepository.listEntriesByEventId(
        swimEventId=eventId,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimEventEntryResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": entries,
        }
    )


@router.post(
    "/events/{eventId}/entries",
    response_model=SwimEventEntryResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSwimEventEntry",
)
async def createSwimEventEntry(
    eventId: uuid.UUID,
    payload: SwimEventEntryCreateReq,
    access: Annotated[
        AccessContext,
        Depends(adminOrTeamManagerOrCoachAccessHandler),
    ],
    nowUtc: Annotated[datetime, Depends(lambda: datetime.now().astimezone())],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
    meetingRepository: Annotated[
        SwimMeetingRepository,
        Depends(swimMeetingRepositoryHandler),
    ],
    entryRepository: Annotated[
        SwimEventEntryRepository,
        Depends(swimEventEntryRepositoryHandler),
    ],
):
    try:
        async with database.transaction(session):
            event = await eventRepository.getEventById(eventId)

            if event is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Swim event not found.",
                )

            meeting = await meetingRepository.getMeetingById(event.meetingId)

            if meeting is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Swim meeting not found.",
                )

            if not access.isAdmin:
                ensureMeetingAcceptsEntries(
                    meetingStatus=meeting.status,
                    entriesOpenAt=meeting.entriesOpenAt,
                    entriesCloseAt=meeting.entriesCloseAt,
                    nowUtc=nowUtc,
                )

            entry = await entryRepository.createEntry(
                swimEventId=eventId,
                federationId=payload.federationId,
                entryTimeMs=payload.entryTimeMs,
                enteredBy=getActorFederationId(access),
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This athlete is already entered in the selected event.",
        ) from exc

    return entry


@router.patch(
    "/entries/{entryId}",
    response_model=SwimEventEntryResp,
    status_code=status.HTTP_200_OK,
    operation_id="updateSwimEventEntry",
)
async def updateSwimEventEntry(
    entryId: uuid.UUID,
    payload: SwimEventEntryUpdateReq,
    access: Annotated[
        AccessContext,
        Depends(adminOrTeamManagerOrCoachAccessHandler),
    ],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    entryRepository: Annotated[
        SwimEventEntryRepository,
        Depends(swimEventEntryRepositoryHandler),
    ],
):
    async with database.transaction(session):
        entry = await entryRepository.getEntryById(entryId)

        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim event entry not found.",
            )

        if not access.isAdmin and entry.enteredBy != getActorFederationId(access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can update only entries created by yourself.",
            )

        entry = await entryRepository.updateEntryTime(
            entry=entry,
            entryTimeMs=payload.entryTimeMs,
            enteredBy=getActorFederationId(access),
        )

    return entry


@router.delete(
    "/entries/{entryId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deleteSwimEventEntry",
)
async def deleteSwimEventEntry(
    entryId: uuid.UUID,
    access: Annotated[
        AccessContext,
        Depends(adminOrTeamManagerOrCoachAccessHandler),
    ],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    entryRepository: Annotated[
        SwimEventEntryRepository,
        Depends(swimEventEntryRepositoryHandler),
    ],
):
    async with database.transaction(session):
        entry = await entryRepository.getEntryById(entryId)

        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim event entry not found.",
            )

        if not access.isAdmin and entry.enteredBy != getActorFederationId(access):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can delete only entries created by yourself.",
            )

        await entryRepository.deleteEntry(entry)

    return {"msg": "Swim event entry deleted successfully."}
