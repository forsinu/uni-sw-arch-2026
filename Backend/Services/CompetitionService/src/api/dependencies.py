from typing import Annotated, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, status, Request
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.db.session import DatabaseHandler
from src.core.security import (
    SecurityHandler,
    AccessTokenPayload,
    FederationRole,
    UserAccountRole,
)
from src.core.env import EnvHandler


tokenHandler = HTTPBearer()


def envHandler(request: Request) -> EnvHandler:
    return request.app.state.env


def secHandler(request: Request) -> SecurityHandler:
    return request.app.state.security


async def dbHandler(request: Request) -> AsyncGenerator[AsyncSession, None]:
    database: DatabaseHandler = request.app.state.database
    async for session in database.getDbSession():
        yield session


class AccessHandler:
    def __init__(
        self,
        fedRoles: list[FederationRole] = None,
        checkAdmin: bool = False,
    ):
        self.allowedFedRoles = fedRoles
        self.checkAdmin = checkAdmin

    def __call__(
        self,
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

        if self.checkAdmin and payload.role != UserAccountRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {UserAccountRole.ADMIN}",
            )

        elif self.allowedFedRoles:
            role = sec.extractFedFields(payload.fed)

            if role not in self.allowedFedRoles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in self.allowedFedRoles]}",
                )

        return payload
