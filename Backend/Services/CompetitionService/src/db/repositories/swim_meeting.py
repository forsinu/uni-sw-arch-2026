from collections.abc import Sequence
from datetime import date, datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swim_meeting import (
    MeetingPoolLength,
    SwimMeeting,
    SwimMeetingStatus,
)


class SwimMeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getMeetingById(
        self,
        meetingId: uuid.UUID,
    ) -> SwimMeeting | None:
        query = select(SwimMeeting).where(SwimMeeting.id == meetingId)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listMeetings(
        self,
        limit: int,
        offset: int,
        status: SwimMeetingStatus | None = None,
        organizerTeamId: uuid.UUID | None = None,
        swimmingPoolId: uuid.UUID | None = None,
        dateFrom: date | None = None,
        dateTo: date | None = None,
    ) -> tuple[int, Sequence[SwimMeeting]]:
        countQuery = select(func.count()).select_from(SwimMeeting)
        dataQuery = select(SwimMeeting)

        if status is not None:
            countQuery = countQuery.where(SwimMeeting.status == status)
            dataQuery = dataQuery.where(SwimMeeting.status == status)

        if organizerTeamId is not None:
            countQuery = countQuery.where(
                SwimMeeting.organizerTeamId == organizerTeamId
            )
            dataQuery = dataQuery.where(SwimMeeting.organizerTeamId == organizerTeamId)

        if swimmingPoolId is not None:
            countQuery = countQuery.where(SwimMeeting.swimmingPoolId == swimmingPoolId)
            dataQuery = dataQuery.where(SwimMeeting.swimmingPoolId == swimmingPoolId)

        if dateFrom is not None:
            countQuery = countQuery.where(SwimMeeting.startDate >= dateFrom)
            dataQuery = dataQuery.where(SwimMeeting.startDate >= dateFrom)

        if dateTo is not None:
            countQuery = countQuery.where(SwimMeeting.startDate <= dateTo)
            dataQuery = dataQuery.where(SwimMeeting.startDate <= dateTo)

        dataQuery = (
            dataQuery.order_by(SwimMeeting.startDate.desc(), SwimMeeting.name.asc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        meetings = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, meetings

    async def createMeeting(
        self,
        name: str,
        poolLength: MeetingPoolLength,
        entriesOpenAt: datetime,
        entriesCloseAt: datetime,
        startDate: date,
        endDate: date,
        organizerTeamId: uuid.UUID | None = None,
        swimmingPoolId: uuid.UUID | None = None,
        status: SwimMeetingStatus = SwimMeetingStatus.UPCOMING,
    ) -> SwimMeeting:
        meeting = SwimMeeting(
            name=name,
            poolLength=poolLength.value,
            status=status,
            entriesOpenAt=entriesOpenAt,
            entriesCloseAt=entriesCloseAt,
            startDate=startDate,
            endDate=endDate,
            organizerTeamId=organizerTeamId,
            swimmingPoolId=swimmingPoolId,
        )

        self.session.add(meeting)
        await self.session.flush()

        return meeting

    async def updateMeeting(
        self,
        meeting: SwimMeeting,
        name: str | None = None,
        poolLength: MeetingPoolLength | None = None,
        entriesOpenAt: datetime | None = None,
        entriesCloseAt: datetime | None = None,
        startDate: date | None = None,
        endDate: date | None = None,
        organizerTeamId: uuid.UUID | None = None,
        swimmingPoolId: uuid.UUID | None = None,
        status: SwimMeetingStatus | None = None,
    ) -> SwimMeeting:
        if name is not None:
            meeting.name = name

        if poolLength is not None:
            meeting.poolLength = poolLength.value

        if entriesOpenAt is not None:
            meeting.entriesOpenAt = entriesOpenAt

        if entriesCloseAt is not None:
            meeting.entriesCloseAt = entriesCloseAt

        if startDate is not None:
            meeting.startDate = startDate

        if endDate is not None:
            meeting.endDate = endDate

        if organizerTeamId is not None:
            meeting.organizerTeamId = organizerTeamId

        if swimmingPoolId is not None:
            meeting.swimmingPoolId = swimmingPoolId

        if status is not None:
            meeting.status = status

        await self.session.flush()

        return meeting

    async def updateMeetingStatus(
        self,
        meeting: SwimMeeting,
        status: SwimMeetingStatus,
    ) -> SwimMeeting:
        meeting.status = status

        await self.session.flush()

        return meeting

    async def deleteMeeting(
        self,
        meeting: SwimMeeting,
    ) -> None:
        await self.session.delete(meeting)
        await self.session.flush()
