from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.login_attempt import LoginAttempt


class LoginAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def createLoginAttempt(
        self,
        usedEmail: str,
        ipAddress: str | None,
        userAgent: str | None,
        wasSuccessful: bool,
    ) -> LoginAttempt:
        loginAttempt = LoginAttempt(
            usedEmail=usedEmail,
            ipAddress=ipAddress,
            userAgent=userAgent,
            wasSuccessful=wasSuccessful,
        )

        self.session.add(loginAttempt)
        await self.session.flush()

        return loginAttempt

    async def listLoginAttempts(
        self,
        limit: int,
        offset: int,
        email: str | None = None,
    ) -> tuple[int, Sequence[LoginAttempt]]:
        countQuery = select(func.count()).select_from(LoginAttempt)

        dataQuery = (
            select(LoginAttempt)
            .order_by(LoginAttempt.attemptedAt.desc())
            .offset(offset)
            .limit(limit)
        )

        if email is not None:
            countQuery = countQuery.where(LoginAttempt.usedEmail == email)

            dataQuery = (
                select(LoginAttempt)
                .where(LoginAttempt.usedEmail == email)
                .order_by(LoginAttempt.attemptedAt.desc())
                .offset(offset)
                .limit(limit)
            )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        loginAttempts = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, loginAttempts

    async def listLoginAttemptsByEmail(
        self,
        usedEmail: str,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[LoginAttempt]]:
        return await self.listLoginAttempts(
            email=usedEmail,
            limit=limit,
            offset=offset,
        )
