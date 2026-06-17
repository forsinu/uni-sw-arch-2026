from collections.abc import Sequence
from datetime import datetime, timezone
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getRefreshTokenByToken(self, token: str) -> RefreshToken | None:
        query = select(RefreshToken).where(RefreshToken.token == token)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getUserSessionById(
        self,
        userAccountId: uuid.UUID,
        sessionId: uuid.UUID,
    ) -> RefreshToken | None:
        query = select(RefreshToken).where(
            RefreshToken.userAccountId == userAccountId,
            RefreshToken.id == sessionId,
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listUserSessions(
        self,
        userAccountId: uuid.UUID,
        onlyActive: bool = True,
        limit: int | None = None,
        offset: int | None = None,
        allSessions: bool = False,
    ) -> tuple[int, Sequence[RefreshToken]]:
        countQuery = (
            select(func.count())
            .select_from(RefreshToken)
            .where(RefreshToken.userAccountId == userAccountId)
        )

        dataQuery = select(RefreshToken).where(
            RefreshToken.userAccountId == userAccountId,
        )

        if onlyActive is True:
            countQuery = countQuery.where(RefreshToken.isActive == True)
            dataQuery = dataQuery.where(RefreshToken.isActive == True)

        if not allSessions:
            limit = limit or 0
            offset = offset or 0
            dataQuery = (
                dataQuery.order_by(RefreshToken.createdAt.desc())
                .offset(offset)
                .limit(limit)
            )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        refreshTokens = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, refreshTokens

    async def createRefreshToken(
        self,
        token: str,
        userAccountId: uuid.UUID,
        expiresAt: datetime,
        ipAddress: str | None,
        userAgent: str | None,
        isActive: bool = True,
    ) -> RefreshToken:
        refreshToken = RefreshToken(
            token=token,
            userAccountId=userAccountId,
            expiresAt=expiresAt,
            ipAddress=ipAddress,
            userAgent=userAgent,
            isActive=isActive,
        )

        self.session.add(refreshToken)
        await self.session.flush()

        return refreshToken

    async def revokeUserSessions(
        self,
        rotatedAt: datetime,
        userAccountId: uuid.UUID | None = None,
        token: str | None = None,
        onlyActive: bool = False,
    ) -> int:
        query = update(RefreshToken)

        if (userAccountId is None) and (token is None):
            return 0

        if userAccountId is not None:
            query = query.where(
                RefreshToken.userAccountId == userAccountId,
            )

        if token is not None:
            query = query.where(RefreshToken.token == token)

        if onlyActive:
            query = query.where(RefreshToken.isActive == True)

        query = query.values(
            isActive=False,
            rotatedAt=rotatedAt,
        )

        result = await self.session.execute(query)

        return result.rowcount or 0

    async def revokeRefreshTokensByIds(
        self,
        refreshTokenIds: list[uuid.UUID],
        rotatedAt: datetime,
    ) -> int:
        if not refreshTokenIds:
            return 0

        query = (
            update(RefreshToken)
            .where(RefreshToken.id.in_(refreshTokenIds))
            .values(
                isActive=False,
                rotatedAt=rotatedAt,
            )
        )

        result = await self.session.execute(query)

        return result.rowcount or 0

    async def revokeOldestSessionsIfLimitExceeded(
        self,
        userAccountId: uuid.UUID,
        maxSessions: int,
        rotatedAt: datetime,
    ) -> int:
        totalCount, activeSessions = await self.listUserSessions(
            userAccountId=userAccountId,
            onlyActive=True,
            allSessions=True,
        )

        if totalCount < maxSessions:
            return 0

        excessSessions = (totalCount - maxSessions) + 1
        refreshTokenIds = [activeSessions[index].id for index in range(excessSessions)]

        return await self.revokeRefreshTokensByIds(
            refreshTokenIds=refreshTokenIds,
            rotatedAt=rotatedAt,
        )

    def normalizeExpiresAt(self, refreshToken: RefreshToken) -> datetime:
        expiresAt = refreshToken.expiresAt

        if expiresAt.tzinfo is None:
            expiresAt = expiresAt.replace(tzinfo=timezone.utc)
            refreshToken.expiresAt = expiresAt

        return expiresAt
