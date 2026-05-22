from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator, Optional
from fastapi import Cookie, Depends, HTTPException, Header, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.util import ClientInfo
from src.db.model import UserAccountRole
from src.core.security import SecurityHandler
from src.db.session import DatabaseHandler
from src.core.environment import EnvironmentHandler


env = EnvironmentHandler()

db = DatabaseHandler(env=env)
sec = SecurityHandler(env=env)

tokenHandler = HTTPBearer()


def envHandler() -> EnvironmentHandler:
    return env


def secHandler() -> SecurityHandler:
    return sec


async def dbHandler() -> AsyncGenerator[AsyncSession, None]:
    async for session in db.getDbSession():
        yield session


def accessAdminHandler(
    at: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
) -> SecurityHandler.AccessTokenPayload:

    try:
        payload = sec.verifyAccessToken(at.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

    userRole = payload.role
    if userRole != UserAccountRole.ADMIN_ACCOUNT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrative privileges required.",
        )

    return payload


def accessHandler(
    at: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
) -> SecurityHandler.AccessTokenPayload:

    try:
        payload = sec.verifyAccessToken(at.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

    return payload


def refreshTokenHandler(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    rt: Annotated[Optional[str], Cookie()] = None,
):

    return rt


def clientInfoHandler(
    req: Request,
    user_agent: Annotated[Optional[str], Header()] = None,
    x_forwarded_for: Annotated[Optional[str], Header()] = None,
) -> ClientInfo:
    clientIp = "Unknown"
    if x_forwarded_for:
        clientIp = x_forwarded_for.split(",")[0].strip()

    elif req.client:
        clientIp = req.client.host

    userAgent = user_agent or "Unknown"

    return ClientInfo(ip=clientIp, userAgent=userAgent)
