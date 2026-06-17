from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated
import uuid

from fastapi import Depends, Header, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.environment import EnvHandler
from src.core.security import (
    AccessTokenPayload,
    FederationRole,
    UserAccountRole,
    ServiceTokenHandler,
)
from src.core.sec import SecurityHandler
from src.db.session import DatabaseHandler
from src.db.repositories import (
    SwimEventEntryRepository,
    SwimEventRepository,
    SwimEventResultRepository,
    SwimMeetingRepository,
)


tokenHandler = HTTPBearer()


@dataclass(frozen=True)
class AccessContext:
    payload: AccessTokenPayload
    isAdmin: bool
    fedRole: FederationRole | None = None
    teamId: uuid.UUID | None = None


def envHandler(request: Request) -> EnvHandler:
    return request.app.state.envHandler


def secHandler(request: Request) -> SecurityHandler:
    return request.app.state.secHandler


def serviceTokenManagerHandler(request: Request) -> ServiceTokenHandler:
    return request.app.state.serviceTokenHandler


def serviceAccessHandler(
    token: str = Header(alias="X-Service-Token"),
    tokenManager: ServiceTokenHandler = Depends(serviceTokenManagerHandler),
) -> None:
    if not tokenManager.verify(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token.",
        )


def dbManagerHandler(request: Request) -> DatabaseHandler:
    return request.app.state.dbHandler


def timeHandler() -> datetime:
    return datetime.now(timezone.utc)


async def dbSessionHandler(
    database: DatabaseHandler = Depends(dbManagerHandler),
) -> AsyncGenerator[AsyncSession, None]:
    async with database.session() as session:
        yield session


def swimMeetingRepositoryHandler(
    session: AsyncSession = Depends(dbSessionHandler),
) -> SwimMeetingRepository:
    return SwimMeetingRepository(session)


def swimEventRepositoryHandler(
    session: AsyncSession = Depends(dbSessionHandler),
) -> SwimEventRepository:
    return SwimEventRepository(session)


def swimEventEntryRepositoryHandler(
    session: AsyncSession = Depends(dbSessionHandler),
) -> SwimEventEntryRepository:
    return SwimEventEntryRepository(session)


def swimEventResultRepositoryHandler(
    session: AsyncSession = Depends(dbSessionHandler),
) -> SwimEventResultRepository:
    return SwimEventResultRepository(session)


class AccessHandler:
    def __init__(
        self,
        fedRoles: Sequence[FederationRole] | None = None,
        adminOnly: bool = False,
        allowAdmin: bool = True,
    ) -> None:
        self.allowedFedRoles = list(fedRoles) if fedRoles is not None else []
        self.adminOnly = adminOnly
        self.allowAdmin = allowAdmin

    def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(tokenHandler),
        security: SecurityHandler = Depends(secHandler),
    ) -> AccessContext:
        try:
            payload = security.verifyAccessToken(credentials.credentials)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(exc)}",
            ) from exc

        isAdmin = payload.role == UserAccountRole.ADMIN

        if self.adminOnly:
            if not isAdmin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrative privileges required.",
                )

            return AccessContext(
                payload=payload,
                isAdmin=True,
            )

        if isAdmin and self.allowAdmin:
            return AccessContext(
                payload=payload,
                isAdmin=True,
            )

        if not self.allowedFedRoles:
            return AccessContext(
                payload=payload,
                isAdmin=False,
            )

        try:
            fedRole, teamId = security.extractFedFields(payload)

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc

        if fedRole not in self.allowedFedRoles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Access denied. Required federation roles: "
                    f"{[role.value for role in self.allowedFedRoles]}"
                ),
            )

        return AccessContext(
            payload=payload,
            isAdmin=False,
            fedRole=fedRole,
            teamId=teamId,
        )


def internalServiceAccessHandler(
    security: Annotated[SecurityHandler, Depends(secHandler)],
    x_internal_service_token: Annotated[str | None, Header()] = None,
) -> None:
    if x_internal_service_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing internal service token.",
        )

    try:
        security.verifiyServiceToken(x_internal_service_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


authenticatedAccessHandler = AccessHandler()

adminAccessHandler = AccessHandler(
    adminOnly=True,
)

teamManagerAccessHandler = AccessHandler(
    fedRoles=[FederationRole.TEAM_MANAGER],
    allowAdmin=False,
)

coachAccessHandler = AccessHandler(
    fedRoles=[FederationRole.COACH],
    allowAdmin=False,
)

teamManagerOrCoachAccessHandler = AccessHandler(
    fedRoles=[
        FederationRole.TEAM_MANAGER,
        FederationRole.COACH,
    ],
    allowAdmin=False,
)

adminOrTeamManagerAccessHandler = AccessHandler(
    fedRoles=[FederationRole.TEAM_MANAGER],
    allowAdmin=True,
)

adminOrCoachAccessHandler = AccessHandler(
    fedRoles=[FederationRole.COACH],
    allowAdmin=True,
)

adminOrTeamManagerOrCoachAccessHandler = AccessHandler(
    fedRoles=[
        FederationRole.TEAM_MANAGER,
        FederationRole.COACH,
    ],
    allowAdmin=True,
)

adminOrRefereeAccessHandler = AccessHandler(
    fedRoles=[FederationRole.REFEREE],
    allowAdmin=True,
)
