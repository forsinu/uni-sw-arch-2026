from collections.abc import Sequence
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swim_event_result import RaceResultStatus, SwimEventResult


class SwimEventResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getResultById(
        self,
        resultId: uuid.UUID,
    ) -> SwimEventResult | None:
        query = select(SwimEventResult).where(SwimEventResult.id == resultId)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getResultByEventAndFederationId(
        self,
        swimEventId: uuid.UUID,
        federationId: str,
    ) -> SwimEventResult | None:
        query = select(SwimEventResult).where(
            SwimEventResult.swimEventId == swimEventId,
            SwimEventResult.federationId == federationId,
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listResultsByEventId(
        self,
        swimEventId: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[SwimEventResult]]:
        countQuery = (
            select(func.count())
            .select_from(SwimEventResult)
            .where(SwimEventResult.swimEventId == swimEventId)
        )

        dataQuery = (
            select(SwimEventResult)
            .where(SwimEventResult.swimEventId == swimEventId)
            .order_by(
                SwimEventResult.finalTimeMs.asc().nulls_last(),
                SwimEventResult.createdAt.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        results = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, results

    async def createResult(
        self,
        swimEventId: uuid.UUID,
        federationId: str,
        status: RaceResultStatus,
        finalTimeMs: int | None = None,
        splitTimesMs: list[int] | None = None,
        disqualificationReason: str | None = None,
    ) -> SwimEventResult:
        result = SwimEventResult(
            swimEventId=swimEventId,
            federationId=federationId,
            status=status,
            finalTimeMs=finalTimeMs,
            splitTimesMs=splitTimesMs or [],
            disqualificationReason=disqualificationReason,
        )

        self.session.add(result)
        await self.session.flush()

        return result

    async def updateResult(
        self,
        result: SwimEventResult,
        status: RaceResultStatus | None = None,
        finalTimeMs: int | None = None,
        splitTimesMs: list[int] | None = None,
        disqualificationReason: str | None = None,
    ) -> SwimEventResult:
        if status is not None:
            result.status = status

        if finalTimeMs is not None:
            result.finalTimeMs = finalTimeMs

        if splitTimesMs is not None:
            result.splitTimesMs = splitTimesMs

        if disqualificationReason is not None:
            result.disqualificationReason = disqualificationReason

        await self.session.flush()

        return result

    async def upsertResult(
        self,
        swimEventId: uuid.UUID,
        federationId: str,
        status: RaceResultStatus,
        finalTimeMs: int | None = None,
        splitTimesMs: list[int] | None = None,
        disqualificationReason: str | None = None,
    ) -> SwimEventResult:
        result = await self.getResultByEventAndFederationId(
            swimEventId=swimEventId,
            federationId=federationId,
        )

        if result is None:
            return await self.createResult(
                swimEventId=swimEventId,
                federationId=federationId,
                status=status,
                finalTimeMs=finalTimeMs,
                splitTimesMs=splitTimesMs,
                disqualificationReason=disqualificationReason,
            )

        return await self.updateResult(
            result=result,
            status=status,
            finalTimeMs=finalTimeMs,
            splitTimesMs=splitTimesMs,
            disqualificationReason=disqualificationReason,
        )

    async def deleteResult(
        self,
        result: SwimEventResult,
    ) -> None:
        await self.session.delete(result)
        await self.session.flush()
