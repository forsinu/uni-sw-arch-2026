from collections.abc import Sequence
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swim_event_entry import SwimEventEntry


class SwimEventEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getEntryById(
        self,
        entryId: uuid.UUID,
    ) -> SwimEventEntry | None:
        query = select(SwimEventEntry).where(SwimEventEntry.id == entryId)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getEntryByEventAndFederationId(
        self,
        swimEventId: uuid.UUID,
        federationId: str,
    ) -> SwimEventEntry | None:
        query = select(SwimEventEntry).where(
            SwimEventEntry.swimEventId == swimEventId,
            SwimEventEntry.federationId == federationId,
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listEntriesByEventId(
        self,
        swimEventId: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[SwimEventEntry]]:
        countQuery = (
            select(func.count())
            .select_from(SwimEventEntry)
            .where(SwimEventEntry.swimEventId == swimEventId)
        )

        dataQuery = (
            select(SwimEventEntry)
            .where(SwimEventEntry.swimEventId == swimEventId)
            .order_by(SwimEventEntry.entryTimeMs.asc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        entries = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, entries

    async def listEntriesByFederationId(
        self,
        federationId: str,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[SwimEventEntry]]:
        countQuery = (
            select(func.count())
            .select_from(SwimEventEntry)
            .where(SwimEventEntry.federationId == federationId)
        )

        dataQuery = (
            select(SwimEventEntry)
            .where(SwimEventEntry.federationId == federationId)
            .order_by(SwimEventEntry.createdAt.desc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        entries = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, entries

    async def createEntry(
        self,
        swimEventId: uuid.UUID,
        federationId: str,
        entryTimeMs: int,
        enteredBy: str,
    ) -> SwimEventEntry:
        entry = SwimEventEntry(
            swimEventId=swimEventId,
            federationId=federationId,
            entryTimeMs=entryTimeMs,
            enteredBy=enteredBy,
        )

        self.session.add(entry)
        await self.session.flush()

        return entry

    async def updateEntryTime(
        self,
        entry: SwimEventEntry,
        entryTimeMs: int,
        enteredBy: str | None = None,
    ) -> SwimEventEntry:
        entry.entryTimeMs = entryTimeMs

        if enteredBy is not None:
            entry.enteredBy = enteredBy

        await self.session.flush()

        return entry

    async def deleteEntry(
        self,
        entry: SwimEventEntry,
    ) -> None:
        await self.session.delete(entry)
        await self.session.flush()
