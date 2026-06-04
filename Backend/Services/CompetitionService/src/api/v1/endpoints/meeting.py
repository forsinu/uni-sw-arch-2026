from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.util import handleDbOp
from src.db.models.swim_event import SwimEvent
from src.db.models.swim_meeting import SwimMeeting
from src.schema.meeting import (
    CreateMeetingReq,
    MeetingInfoResp,
    PaginatedMeetingsResp,
    UpdateMeetingInfoReq,
    UpdateSwimEventReq,
)
from src.core.security import AccessTokenPayload, FederationRole, UserAccountRole
from src.api.dependencies import AccessHandler, dbHandler

router = APIRouter()


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def createMeeting(
    payload: CreateMeetingReq,
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[FederationRole.TEAM_MANAGER],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
):

    meeting = SwimMeeting(
        name=payload.name,
        poolLength=payload.poolLength,
        entriesOpenAt=payload.entriesOpenAt,
        entriesCloseAt=payload.entriesCloseAt,
        startAt=payload.startAt,
        endAt=payload.endAt,
        organizedBy=payload.organizedBy,
        createdBy=payload.createdBy,
        swimmingPoolId=payload.swimmingPoolId,
        events=[
            SwimEvent(distance=e.distance, stroke=e.stroke) for e in payload.swimEvents
        ],
    )

    async with handleDbOp(session=db, integrityMsg="This meeting already exists."):
        db.add(meeting)
        await db.commit()

    return {"id": meeting.id}


@router.patch("/update/{meetingId}", status_code=status.HTTP_200_OK)
async def updateMeetingInfo(
    meetingId: uuid.UUID,
    payload: UpdateMeetingInfoReq,
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[FederationRole.TEAM_MANAGER],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
):
    data = payload.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update.",
        )

    stmt = update(SwimMeeting).where(SwimMeeting.id == meetingId)

    if at.role != UserAccountRole.ADMIN:
        stmt = stmt.where(SwimMeeting.createdBy == at.sub)

    stmt = stmt.values(**data)

    async with handleDbOp(
        session=db,
        integrityMsg="Failed to update meeting info.",
    ):
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Swim meeting not found or you do not have permission to modify it.",
            )

    return {"updated_fields": list(data.keys())}


@router.patch("/update/{meetingId}/events", status_code=status.HTTP_200_OK)
async def updateMeetingEvents(
    meetingId: uuid.UUID,
    payload: UpdateSwimEventReq,
    at: Annotated[
        AccessTokenPayload,
        Depends(
            AccessHandler(
                fedRoles=[FederationRole.TEAM_MANAGER],
                checkAdmin=True,
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(dbHandler)],
):
    if at.role != UserAccountRole.ADMIN:
        query = (
            select(SwimMeeting)
            .where(
                SwimMeeting.id == meetingId,
                SwimMeeting.createdBy == at.sub,
            )
            .options(selectinload(SwimMeeting.swimEvents))
        )
    else:
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
                detail="The meeting doesn't exist or you aren't authorized to modify it.",
            )

        if payload.removeEvents:
            meeting.swimEvents = [
                event
                for event in meeting.swimEvents
                if event.id not in payload.removeEvents
            ]

        if payload.addEvents:
            for newEvent in payload.addEvents:
                meeting.swimEvents.append(
                    SwimEvent(
                        distance=newEvent.distance,
                        stroke=newEvent.stroke,
                    )
                )

        await db.commit()

    return {
        "removed": len(payload.removeEvents),
        "added": len(payload.addEvents),
    }


@router.get(
    "/meetings",
    response_model=PaginatedMeetingsResp,
    status_code=status.HTTP_200_OK,
)
async def getMeetings(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    off: Annotated[int, Query()] = 0,
    lim: Annotated[int, Query()] = 20,
):
    countQuery = select(func.count()).select_from(SwimMeeting)
    query = (
        select(
            SwimMeeting.id,
            SwimMeeting.name,
            SwimMeeting.startAt,
        )
        .select_from(SwimMeeting)
        .order_by(SwimMeeting.startAt.desc())
        .offset(off)
        .limit(lim)
    )

    async with handleDbOp(session=db):
        totalCount = (await db.execute(countQuery)).scalar_one()
        meetings = (await db.execute(query)).scalars().all()

    return PaginatedMeetingsResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": lim,
                "offset": off,
                "hasMore": (off + lim) < totalCount,
            },
            "results": meetings,
        }
    )


@router.get(
    "/meetings/{meetingId}",
    response_model=MeetingInfoResp,
    status_code=status.HTTP_200_OK,
)
async def getMeeting(
    meetingId: uuid.UUID,
    db: Annotated[AsyncSession, Depends(dbHandler)],
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
            detail="The requested swim meeting does not exist.",
        )

    return meeting
