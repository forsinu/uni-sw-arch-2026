from collections.abc import Sequence
from datetime import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swim_event import (
    RaceDistance,
    RaceGender,
    RaceStroke,
    SwimEvent,
)


class SwimEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getEventById(
        self,
        eventId: uuid.UUID,
    ) -> SwimEvent | None:
        query = select(SwimEvent).where(SwimEvent.id == eventId)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listEventsByMeetingId(
        self,
        meetingId: uuid.UUID,
        limit: int,
        offset: int,
        stroke: RaceStroke | None = None,
        gender: RaceGender | None = None,
        distance: RaceDistance | None = None,
    ) -> tuple[int, Sequence[SwimEvent]]:
        countQuery = (
            select(func.count())
            .select_from(SwimEvent)
            .where(SwimEvent.meetingId == meetingId)
        )

        dataQuery = select(SwimEvent).where(SwimEvent.meetingId == meetingId)

        if stroke is not None:
            countQuery = countQuery.where(SwimEvent.stroke == stroke)
            dataQuery = dataQuery.where(SwimEvent.stroke == stroke)

        if gender is not None:
            countQuery = countQuery.where(SwimEvent.gender == gender)
            dataQuery = dataQuery.where(SwimEvent.gender == gender)

        if distance is not None:
            countQuery = countQuery.where(SwimEvent.distance == distance.value)
            dataQuery = dataQuery.where(SwimEvent.distance == distance.value)

        dataQuery = (
            dataQuery.order_by(SwimEvent.startAt.asc()).offset(offset).limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        events = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, events

    async def createEvent(
        self,
        meetingId: uuid.UUID,
        distance: RaceDistance,
        stroke: RaceStroke,
        gender: RaceGender,
        startAt: datetime,
    ) -> SwimEvent:
        event = SwimEvent(
            meetingId=meetingId,
            distance=distance.value,
            stroke=stroke,
            gender=gender,
            startAt=startAt,
        )

        self.session.add(event)
        await self.session.flush()

        return event

    async def updateEvent(
        self,
        event: SwimEvent,
        distance: RaceDistance | None = None,
        stroke: RaceStroke | None = None,
        gender: RaceGender | None = None,
        startAt: datetime | None = None,
    ) -> SwimEvent:
        if distance is not None:
            event.distance = distance.value

        if stroke is not None:
            event.stroke = stroke

        if gender is not None:
            event.gender = gender

        if startAt is not None:
            event.startAt = startAt

        await self.session.flush()

        return event

    async def deleteEvent(
        self,
        event: SwimEvent,
    ) -> None:
        await self.session.delete(event)
        await self.session.flush()
