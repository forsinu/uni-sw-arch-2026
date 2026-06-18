from collections.abc import Sequence
import uuid

from sqlalchemy import delete, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swim_meeting_referee import SwimMeetingReferee


class SwimMeetingRefereeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def addRefereeToMeeting(
        self,
        meetingId: uuid.UUID,
        refereeFederationId: str,
        assignedBy: uuid.UUID | None = None,
    ) -> SwimMeetingReferee:
        referee = SwimMeetingReferee(
            meetingId=meetingId,
            refereeFederationId=refereeFederationId,
            assignedBy=assignedBy,
        )

        self.session.add(referee)
        await self.session.flush()

        return referee

    async def removeRefereeFromMeeting(
        self,
        meetingId: uuid.UUID,
        refereeFederationId: str,
    ) -> bool:
        query = delete(SwimMeetingReferee).where(
            SwimMeetingReferee.meetingId == meetingId,
            SwimMeetingReferee.refereeFederationId == refereeFederationId,
        )

        result = await self.session.execute(query)

        return result.rowcount > 0

    async def listMeetingReferees(
        self,
        meetingId: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[SwimMeetingReferee]]:
        countQuery = (
            select(func.count())
            .select_from(SwimMeetingReferee)
            .where(SwimMeetingReferee.meetingId == meetingId)
        )

        dataQuery = (
            select(SwimMeetingReferee)
            .where(SwimMeetingReferee.meetingId == meetingId)
            .order_by(SwimMeetingReferee.createdAt.asc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = await self.session.scalar(countQuery)

        result = await self.session.execute(dataQuery)

        return totalRecords or 0, result.scalars().all()

    async def isRefereeAssignedToMeeting(
        self,
        meetingId: uuid.UUID,
        refereeFederationId: str,
    ) -> bool:
        query = select(
            exists().where(
                SwimMeetingReferee.meetingId == meetingId,
                SwimMeetingReferee.refereeFederationId == refereeFederationId,
            )
        )

        result = await self.session.execute(query)

        return bool(result.scalar_one())

    async def listRefereeMeetings(
        self,
        refereeFederationId: str,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[SwimMeetingReferee]]:
        countQuery = (
            select(func.count())
            .select_from(SwimMeetingReferee)
            .where(SwimMeetingReferee.refereeFederationId == refereeFederationId)
        )

        dataQuery = (
            select(SwimMeetingReferee)
            .where(SwimMeetingReferee.refereeFederationId == refereeFederationId)
            .order_by(SwimMeetingReferee.createdAt.asc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = await self.session.scalar(countQuery)

        result = await self.session.execute(dataQuery)

        return totalRecords or 0, result.scalars().all()
