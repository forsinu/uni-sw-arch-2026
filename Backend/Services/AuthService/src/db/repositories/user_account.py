from collections.abc import Sequence
from datetime import datetime
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user_account import (
    UserAccount,
    UserAccountRole,
    UserAccountStatus,
)


class UserAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getUserById(
        self,
        userId: uuid.UUID,
        isActive: bool = False,
    ) -> UserAccount | None:
        query = select(UserAccount).where(UserAccount.id == userId)

        if isActive:
            query = query.where(UserAccount.accountStatus == UserAccountStatus.ACTIVE)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def setUserFedId(
        self,
        newFederationId: str,
        oldFederationId: str | None = None,
    ) -> UserAccount | None:
        stmt = update(UserAccount)

        if oldFederationId is not None:
            stmt = stmt.where(UserAccount.federationId == oldFederationId)

        stmt = stmt.values(federationId=newFederationId)
        result = await self.session.execute(stmt)

        return result.rowcount > 0

    async def getUserByEmail(
        self,
        email: str,
        isActive: bool = False,
    ) -> UserAccount | None:
        query = select(UserAccount).where(UserAccount.email == email)

        if isActive:
            query = query.where(UserAccountStatus == UserAccountStatus.ACTIVE)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getUserEmailAndUsernameById(
        self,
        userId: uuid.UUID,
    ) -> tuple[str | None, str] | None:
        query = select(
            UserAccount.email,
            UserAccount.username,
        ).where(UserAccount.id == userId)

        result = await self.session.execute(query)
        row = result.one_or_none()

        if row is None:
            return None

        return row.email, row.username

    async def getUserByUsername(
        self,
        username: str,
        isActive: bool = False,
    ):
        query = select(UserAccount).where(UserAccount.username == username)

        if isActive:
            query = query.where(UserAccountStatus == UserAccountStatus.ACTIVE)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getUserByUsernameOrEmail(
        self,
        usernameOrEmail: str,
    ) -> UserAccount | None:
        stmt = select(UserAccount).where(
            or_(
                UserAccount.username == usernameOrEmail,
                UserAccount.email == usernameOrEmail,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def getAdminUser(self) -> UserAccount | None:
        query = (
            select(UserAccount)
            .where(UserAccount.userRole == UserAccountRole.ADMIN)
            .order_by(UserAccount.createdAt.asc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listUsers(
        self,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[UserAccount]]:
        countQuery = select(func.count()).select_from(UserAccount)

        dataQuery = (
            select(UserAccount)
            .order_by(UserAccount.createdAt.desc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        users = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, users

    async def listUsersByStatus(
        self,
        accountStatus: UserAccountStatus,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[UserAccount]]:
        countQuery = (
            select(func.count())
            .select_from(UserAccount)
            .where(UserAccount.accountStatus == accountStatus)
        )

        dataQuery = (
            select(UserAccount)
            .where(UserAccount.accountStatus == accountStatus)
            .order_by(UserAccount.createdAt.desc())
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        users = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, users

    async def createUser(
        self,
        username: str,
        hashedPassword: str,
        userRole: UserAccountRole = UserAccountRole.DEFAULT,
        accountStatus: UserAccountStatus = UserAccountStatus.ACTIVE,
        federationId: str | None = None,
        createdAt: datetime | None = None,
        email: str | None = None,
    ) -> UserAccount:
        user = UserAccount(
            email=email,
            username=username,
            password=hashedPassword,
            userRole=userRole,
            federationId=federationId,
            accountStatus=accountStatus,
        )

        if createdAt is not None:
            user.createdAt = createdAt

        self.session.add(user)

        # Needed when caller must immediately use user.id.
        await self.session.flush()

        return user

    async def updateUserPassword(
        self,
        user: UserAccount,
        hashedPassword: str,
        updatedAt: datetime | None = None,
    ) -> UserAccount:
        user.password = hashedPassword

        if updatedAt is not None:
            user.updatedAt = updatedAt

        await self.session.flush()

        return user

    async def updateUserStatus(
        self,
        user: UserAccount,
        accountStatus: UserAccountStatus,
        updatedAt: datetime | None = None,
    ) -> UserAccount:
        user.accountStatus = accountStatus

        if updatedAt is not None:
            user.updatedAt = updatedAt

        await self.session.flush()

        return user

    async def updateUserEmail(
        self,
        user: UserAccount,
        email: str,
        updatedAt: datetime | None = None,
    ) -> UserAccount:
        user.email = email

        if updatedAt is not None:
            user.updatedAt = updatedAt

        await self.session.flush()

        return user
