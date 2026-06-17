# src/api/dependencies.py

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from logging import Logger
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.environment import EnvHandler
from src.core.log import LoggerHandler
from src.core.sec import SecurityHandler
from src.schemas.common import ClientInfo

from src.db.models.refresh_token import RefreshToken
from src.db.models.user_account import UserAccountRole
from src.db.session import DatabaseHandler
from src.db.repositories import (
    LoginAttemptRepository,
    RefreshTokenRepository,
    UserAccountHistoryRepository,
    UserAccountRepository,
)


tokenHandler = HTTPBearer()


def envHandler(request: Request) -> EnvHandler:
    return request.app.state.env


def logHandler(request: Request) -> LoggerHandler:
    return request.app.state.loggerHandler


def loggerHandler(
    loggerManager: Annotated[LoggerHandler, Depends(logHandler)],
) -> Logger:
    return loggerManager.app


def securityHandler(request: Request) -> SecurityHandler:
    return request.app.state.secHandler


def databaseHandler(request: Request) -> DatabaseHandler:
    return request.app.state.dbHandler


async def dbSessionHandler(
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
) -> AsyncGenerator[AsyncSession, None]:
    async with database.session() as session:
        yield session


def userAccountRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> UserAccountRepository:
    return UserAccountRepository(session)


def userAccountHistoryRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> UserAccountHistoryRepository:
    return UserAccountHistoryRepository(session)


def refreshTokenRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def loginAttemptRepositoryHandler(
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
) -> LoginAttemptRepository:
    return LoginAttemptRepository(session)


def accessHandler(
    token: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
    security: Annotated[SecurityHandler, Depends(securityHandler)],
):
    try:
        return security.verifyAccessToken(token.credentials)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(exc)}",
        ) from exc


def accessAdminHandler(
    payload: Annotated[object, Depends(accessHandler)],
):
    if payload.role != UserAccountRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrative privileges required.",
        )

    return payload


def refreshCookieHandler(
    rt: Annotated[str | None, Cookie()] = None,
) -> str:
    if rt is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing. Please sign in again.",
        )

    return rt


def clientInfoHandler(
    request: Request,
    userAgent: Annotated[str | None, Header(alias="User-Agent")] = None,
    xForwardedFor: Annotated[str | None, Header(alias="X-Forwarded-For")] = None,
) -> ClientInfo:
    clientIp = None

    if xForwardedFor:
        clientIp = xForwardedFor.split(",")[0].strip()

    elif request.client:
        clientIp = request.client.host

    return ClientInfo(ip=clientIp, ua=userAgent)


def timeHandler() -> datetime:
    return datetime.now(timezone.utc)
