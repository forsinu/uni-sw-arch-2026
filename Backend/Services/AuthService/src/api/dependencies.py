from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Cookie, Depends, Response, status, Request, Header
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.db.models.refresh_token import RefreshToken
from src.db.models.user_account import UserAccountRole
from src.db.session import DatabaseHandler
from src.core.security import SecurityHandler, AccessTokenPayload
from src.core.env import EnvHandler
from src.core.util import handleDbOp, ClientInfo


tokenHandler = HTTPBearer()


def envHandler(request: Request) -> EnvHandler:
    return request.app.state.env


def secHandler(request: Request) -> SecurityHandler:
    return request.app.state.security


async def dbHandler(request: Request) -> AsyncGenerator[AsyncSession, None]:
    database: DatabaseHandler = request.app.state.database
    async for session in database.getDbSession():
        yield session


# Use Access Token to verify is the user can request something
def accessHandler(
    at: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
) -> AccessTokenPayload:

    try:
        payload = sec.verifyAccessToken(at.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

    return payload


# Use Access Token to verify the role of the user!!
def accessAdminHandler(
    payload: Annotated[AccessTokenPayload, Depends(accessHandler)],
) -> AccessTokenPayload:

    if payload.role != UserAccountRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrative privileges required.",
        )

    return payload


async def refreshHandler(
    response: Response,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    rt: Annotated[Optional[str], Cookie()] = None,
) -> RefreshToken:

    nowUtc = datetime.now(timezone.utc)

    # The Refresh Token is absent
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token missing. Please login again.",
        )

    async with handleDbOp(session=db, errorMsg="Internal Server Error."):
        query = await db.execute(select(RefreshToken).where(RefreshToken.token == rt))
        dbToken = query.scalar_one_or_none()

    if not dbToken:
        sec.revokeRefreshToken(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session. Please sign in again.",
        )

    if not dbToken.isActive:
        sec.revokeRefreshToken(response)

        async with handleDbOp(session=db, errorMsg="Internal Server Error."):
            await db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.userAccountId == dbToken.userAccountId,
                    RefreshToken.isActive == True,
                )
                .values(isActive=False, rotatedAt=nowUtc)
            )

            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session. Please sign in again.",
        )

    if dbToken.expiresAt.tzinfo is None:
        dbToken.expiresAt = dbToken.expiresAt.replace(tzinfo=timezone.utc)

    if nowUtc >= dbToken.expiresAt:
        sec.revokeRefreshToken(response)

        dbToken.isActive = False
        dbToken.rotatedAt = nowUtc

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session. Please sign in again.",
        )

    return dbToken


def clientInfoHandler(
    req: Request,
    user_agent: Annotated[Optional[str], Header()] = None,
    x_forwarded_for: Annotated[Optional[str], Header()] = None,
) -> ClientInfo:
    clientIp = None
    if x_forwarded_for:
        clientIp = x_forwarded_for.split(",")[0].strip()

    elif req.client:
        clientIp = req.client.host

    userAgent = user_agent or None

    return ClientInfo(ip=clientIp, ua=userAgent)


def timeHandler():
    return datetime.now(timezone.utc)
