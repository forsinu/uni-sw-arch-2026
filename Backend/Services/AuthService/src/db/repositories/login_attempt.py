from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.login_attempt import LoginAttempt


class LoginAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def createLoginAttempt(
        self,
        usedEmailOrUsername: str,
        ipAddress: str | None,
        userAgent: str | None,
        wasSuccessful: bool,
    ) -> LoginAttempt:
        loginAttempt = LoginAttempt(
            usedEmailOrUsername=usedEmailOrUsername,
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
        emailOrUsername: str | None = None,
    ) -> tuple[int, Sequence[LoginAttempt]]:
        countQuery = select(func.count()).select_from(LoginAttempt)

        dataQuery = (
            select(LoginAttempt)
            .order_by(LoginAttempt.attemptedAt.desc())
            .offset(offset)
            .limit(limit)
        )

        if emailOrUsername is not None:
            countQuery = countQuery.where(
                LoginAttempt.usedEmailOrUsername == emailOrUsername
            )

            dataQuery = dataQuery.where(
                LoginAttempt.usedEmailOrUsername == emailOrUsername
            )

        totalRecords = await self.session.scalar(countQuery)

        result = await self.session.execute(dataQuery)
        loginAttempts = result.scalars().all()

        return totalRecords or 0, loginAttempts

    async def listLoginAttemptsByEmailOrUsername(
        self,
        limit: int,
        offset: int,
        usedEmailOrUsername: str | None = None,
    ) -> tuple[int, Sequence[LoginAttempt]]:
        return await self.listLoginAttempts(
            emailOrUsername=usedEmailOrUsername,
            limit=limit,
            offset=offset,
        )

    async def listLoginAttemptsByUserIdentity(
        self,
        username: str,
        email: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[LoginAttempt]]:
        identifiers = [username]

        if email is not None:
            identifiers.append(email)

        countQuery = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(LoginAttempt.usedEmailOrUsername.in_(identifiers))
        )

        dataQuery = (
            select(LoginAttempt)
            .where(LoginAttempt.usedEmailOrUsername.in_(identifiers))
            .order_by(LoginAttempt.attemptedAt.desc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = await self.session.scalar(countQuery)

        result = await self.session.execute(dataQuery)
        loginAttempts = result.scalars().all()

        return totalRecords or 0, loginAttempts
