from collections.abc import Sequence
from datetime import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user_account import (
    UserAccountHistory,
    UserAccountStatus,
)


class UserAccountHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def createHistoryEntry(
        self,
        userAccountId: uuid.UUID,
        statusChangedTo: UserAccountStatus,
        changedBy: uuid.UUID | None,
        reason: str | None = None,
        changedAt: datetime | None = None,
    ) -> UserAccountHistory:
        historyEntry = UserAccountHistory(
            userAccountId=userAccountId,
            statusChangedTo=statusChangedTo,
            changedBy=changedBy,
            reason=reason,
        )

        if changedAt is not None:
            historyEntry.changedAt = changedAt

        self.session.add(historyEntry)
        await self.session.flush()

        return historyEntry

    async def listUserHistory(
        self,
        userAccountId: uuid.UUID,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[UserAccountHistory]]:
        countQuery = (
            select(func.count())
            .select_from(UserAccountHistory)
            .where(UserAccountHistory.userAccountId == userAccountId)
        )

        dataQuery = (
            select(UserAccountHistory)
            .where(UserAccountHistory.userAccountId == userAccountId)
            .order_by(UserAccountHistory.changedAt.desc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        historyEntries = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, historyEntries
