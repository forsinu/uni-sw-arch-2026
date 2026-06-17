from collections.abc import AsyncGenerator
from dataclasses import dataclass
from logging import Logger
from typing import Annotated
import uuid

from fastapi import Depends, Header, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.environment import EnvHandler
from src.core.log import LoggerHandler
from src.core.sec import SecurityHandler
from src.core.security.models import AccessTokenPayload, UserAccountRole
from src.core.security.service_auth import ServiceTokenHandler

from src.db.models.federation_members import FederationRole
from src.db.session import DatabaseHandler

from src.db.repositories.federation_member import FederationMemberRepository
from src.db.repositories.swimming_pool import SwimmingPoolRepository
from src.db.repositories.swimming_team import SwimmingTeamRepository


tokenHandler = HTTPBearer()


@dataclass(frozen=True)
class AccessContext:
    payload: AccessTokenPayload
    isAdmin: bool
    fedRole: FederationRole | None = None
    teamId: uuid.UUID | None = None


def envHandler(request: Request) -> EnvHandler:
    return request.app.state.envHandler


def logHandler(request: Request) -> LoggerHandler:
    return request.app.state.loggerHandler


def loggerHandler(
    loggerManager: Annotated[LoggerHandler, Depends(logHandler)],
) -> Logger:
    return loggerManager.app


def secHandler(request: Request) -> SecurityHandler:
    return request.app.state.secHandler


def serviceTokenManagerHandler(request: Request) -> ServiceTokenHandler:
    return request.app.state.serviceTokenHandler


def serviceAccessHandler(
    token: Annotated[str, Header(alias="X-Service-Token")],
    tokenManager: Annotated[
        ServiceTokenHandler,
        Depends(serviceTokenManagerHandler),
    ],
) -> None:
    if not tokenManager.verify(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token.",
        )


def dbManagerHandler(request: Request) -> DatabaseHandler:
    return request.app.state.dbHandler


async def dbSessionHandler(
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
) -> AsyncGenerator[AsyncSession, None]:
    async with database.session() as session:
        yield session


def swimmingTeamRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> SwimmingTeamRepository:
    return SwimmingTeamRepository(session)


def swimmingPoolRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> SwimmingPoolRepository:
    return SwimmingPoolRepository(session)


def federationMemberRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> FederationMemberRepository:
    return FederationMemberRepository(session)


def accessHandler(
    token: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
    security: Annotated[SecurityHandler, Depends(secHandler)],
) -> AccessTokenPayload:
    try:
        return security.verifyAccessToken(token.credentials)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(exc)}",
        ) from exc


def adminAccessHandler(
    payload: Annotated[AccessTokenPayload, Depends(accessHandler)],
) -> AccessTokenPayload:
    if payload.role != UserAccountRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )

    return payload


def adminOrTeamManagerAccessHandler(
    payload: Annotated[AccessTokenPayload, Depends(accessHandler)],
    security: Annotated[SecurityHandler, Depends(secHandler)],
) -> AccessContext:
    if payload.role == UserAccountRole.ADMIN:
        return AccessContext(
            payload=payload,
            isAdmin=True,
        )

    try:
        fedRole, teamId = security.extractFedFields(payload)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if fedRole != FederationRole.TEAM_MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team-manager privileges required.",
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
