from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, HTTPException, Query, status, Depends

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.event_result import (
    SwimEventResult,
)
from src.core.util import handleDbOp
from src.db.models.swim_meeting import SwimMeeting
from src.db.models.event_entries import SwimEventEntry
from src.schema.event import (
    InsertResultsReq,
    PaginatedMeetingEntriesResp,
    PaginatedMeetingResultsResp,
    SubscribeAthleteReq,
    UpdateMeetingEntryReq,
)
from src.core.security import (
    AccessTokenPayload,
    FederationRole,
    SecurityHandler,
    UserAccountRole,
)
from src.api.dependencies import AccessHandler, dbHandler, secHandler


router = APIRouter()


@router.post("/entries", status_code=status.HTTP_200_OK)
async def subscribeAthlete(
    payload: SubscribeAthleteReq,
    at: Annotated[
        AccessTokenPayload,
        Depends(AccessHandler(fedRoles=[FederationRole.COACH])),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):
    _, coachTeamId = sec.extractFedFields(token=at)
    athleteRole, athleteTeamId = sec.extractFedFields(token=payload.athleteFedId)

    if athleteRole != FederationRole.ATHLETE or coachTeamId != athleteTeamId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. The target ID does not belong to an athlete, or the athlete belongs to a different team than the authenticated coach.",
        )

    payloadEventsMap = {entry.eventId: entry.entryTime for entry in payload.events}
    if not payloadEventsMap:
        return

    async with handleDbOp(session=db):
        query = (
            select(SwimMeeting)
            .where(SwimMeeting.id == payload.meetingId)
            .options(selectinload(SwimMeeting.swimEvents))
        )
        result = await db.execute(query)
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Swim meeting with ID {payload.meetingId} could not be found.",
            )

        entries = []
        for event in meeting.swimEvents:
            if event.id in payloadEventsMap:
                entries.append(
                    SwimEventEntry(
                        federationId=payload.athelteFedId,
                        entryTime=payloadEventsMap[event.id],
                        enteredBy=at.fed,
                        swimEventId=event.id,
                    )
                )

        if entries:
            db.add_all(entries)
            await db.commit()

    return


@router.get(
    "/entries/{meetingId}",
    response_model=PaginatedMeetingEntriesResp,
    status_code=status.HTTP_200_OK,
)
async def getMeetingEntries(
    meetingId: uuid.UUID,
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[
                    FederationRole.ATHLETE,
                    FederationRole.COACH,
                ],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    off: Annotated[int, Query()] = 0,
    lim: Annotated[int, Query()] = 20,
    event: Annotated[Optional[uuid.UUID], Query()] = None,
):
    query = (
        select(SwimMeeting)
        .where(SwimMeeting.id == meetingId)
        .options(selectinload(SwimMeeting.swimEvents))
    )

    async with handleDbOp(session=db):
        result = await db.execute(query)
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Swim meeting with ID {meetingId} could not be found.",
            )

        fedRole, fedTeam = sec.extractFedFields(at.fed)
        meetEventIds = [e.id for e in meeting.swimEvents]

        if event:
            if event not in meetEventIds:
                return {
                    "metadata": {
                        "totalRecords": 0,
                        "limit": lim,
                        "offset": off,
                        "hasMore": False,
                    },
                    "entries": [],
                }
            targetEventIds = [event]
        else:
            targetEventIds = meetEventIds

        if not targetEventIds:
            return {
                "metadata": {
                    "totalRecords": 0,
                    "limit": lim,
                    "offset": off,
                    "hasMore": False,
                },
                "entries": [],
            }

        stmt = select(
            SwimEventEntry,
            func.count().over().label("total_count"),
        ).where(SwimEventEntry.swimEventId.in_(targetEventIds))

        if at.role == UserAccountRole.ADMIN:
            pass
        elif fedRole == FederationRole.COACH:
            stmt = stmt.where(SwimEventEntry.federationId.like(f"%{fedTeam}%"))
        elif fedRole == FederationRole.ATHLETE:
            stmt = stmt.where(SwimEventEntry.federationId == at.fed)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. The authenticated user role context is unauthorized to view these entries.",
            )

        paginatedStmt = stmt.offset(off).limit(lim)
        res = await db.execute(paginatedStmt)
        rows = res.all()

    totalCount = rows[0].total_count if rows else 0
    entries = [row[0] for row in rows]

    # Fixed: Changed dictionary key from 'results' to 'entries' to avoid validation error
    return PaginatedMeetingEntriesResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": lim,
                "offset": off,
                "hasMore": (off + lim) < totalCount,
            },
            "entries": entries,
        }
    )


@router.patch(
    "/entries/{entryId}",
    status_code=status.HTTP_200_OK,
)
async def updateEntry(
    entryId: uuid.UUID,
    payload: UpdateMeetingEntryReq,
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[FederationRole.COACH],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):
    async with handleDbOp(session=db):
        query = select(SwimEventEntry).where(SwimEventEntry.id == entryId)
        result = await db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Swim event entry with ID {entryId} could not be found.",
            )

        if at.role != UserAccountRole.ADMIN:
            _, coachFedTeam = sec.extractFedFields(token=at)
            _, athleteFedTeam = sec.extractFedFields(entry.federationId)

            if athleteFedTeam != coachFedTeam:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Coaches can only modify event entries for athletes belonging to their own team.",
                )

        entry.entryTime = payload.entryTime
        await db.commit()

    return {"msg": "Event entry updated successfully."}


@router.delete("/entries/{entryId}", status_code=status.HTTP_200_OK)
async def deleteEntry(
    entryId: uuid.UUID,
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[FederationRole.COACH],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):
    async with handleDbOp(session=db):
        query = select(SwimEventEntry).where(SwimEventEntry.id == entryId)
        result = await db.execute(query)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Swim event entry with ID {entryId} could not be found.",
            )

        if at.role != UserAccountRole.ADMIN:
            _, coachFedTeam = sec.extractFedFields(token=at)
            _, athleteFedTeam = sec.extractFedFields(entry.federationId)

            if athleteFedTeam != coachFedTeam:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Coaches can only delete event entries for athletes belonging to their own team.",
                )

        await db.delete(entry)
        await db.commit()

    return {"msg": "Event entry deleted successfully."}


@router.get(
    "/results/{meetingId}",
    response_model=PaginatedMeetingResultsResp,
    status_code=status.HTTP_200_OK,
)
async def getMeetingResults(
    meetingId: uuid.UUID,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    off: Annotated[int, Query()] = 0,
    lim: Annotated[int, Query()] = 20,
    event: Annotated[Optional[uuid.UUID], Query()] = None,
):
    query = (
        select(SwimMeeting)
        .where(SwimMeeting.id == meetingId)
        .options(selectinload(SwimMeeting.swimEvents))
    )

    async with handleDbOp(session=db):
        result = await db.execute(query)
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Swim meeting with ID {meetingId} could not be found.",
            )

        meetEventIds = [e.id for e in meeting.swimEvents]

        if event:
            if event not in meetEventIds:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            targetEventIds = [event]
        else:
            targetEventIds = meetEventIds

        if not targetEventIds:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        stmt = select(SwimEventEntry).where(
            SwimEventEntry.swimEventId.in_(targetEventIds)
        )

        countStmt = select(func.count()).select_from(stmt.subquery())
        totalCount = await db.scalar(countStmt) or 0

        query = stmt.offset(off).limit(lim)
        result = await db.execute(result)
        results = result.scalars().all()

    return PaginatedMeetingEntriesResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": lim,
                "offset": off,
                "hasMore": (off + lim) < totalCount,
            },
            "results": results,
        }
    )


@router.post("/results", status_code=status.HTTP_200_OK)
async def addEventResults(
    payload: list[InsertResultsReq],
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[FederationRole.REFEREE],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
):
    if not payload:
        return {"msg": "No results were provided for insertion."}

    data = [res.model_dump() for res in payload]

    async with handleDbOp(session=db):
        await db.execute(insert(SwimEventResult), data)
        await db.commit()

    return {"msg": "All race results were successfully inserted."}
