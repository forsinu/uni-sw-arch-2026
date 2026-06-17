# src/api/v1/user.py

from datetime import datetime
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    accessHandler,
    databaseHandler,
    dbSessionHandler,
    loginAttemptRepositoryHandler,
    refreshTokenRepositoryHandler,
    securityHandler,
    timeHandler,
    userAccountHistoryRepositoryHandler,
    userAccountRepositoryHandler,
)
from src.core.sec import AccessTokenPayload, SecurityHandler
from src.db.models.user_account import UserAccountStatus
from src.db.repositories import (
    LoginAttemptRepository,
    RefreshTokenRepository,
    UserAccountHistoryRepository,
    UserAccountRepository,
)
from src.db.session import DatabaseHandler
from src.schemas.user import (
    DeleteUserReq,
    PaginatedLoginAttemptResp,
    PaginatedRefreshTokenResp,
    RefreshTokenResp,
    ResetPasswdReq,
    UserAccountResp,
)

from src.schemas.common import MessageResp


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserAccountResp,
    status_code=status.HTTP_200_OK,
    operation_id="getCurrentUser",
)
async def getCurrentUser(
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    userRepository: Annotated[
        UserAccountRepository,
        Depends(userAccountRepositoryHandler),
    ],
):
    user = await userRepository.getUserById(accessToken.sub, isActive=True)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found or account is no longer active.",
        )

    return user


@router.delete(
    "/me",
    response_model=MessageResp,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="archiveCurrentUser",
)
async def archiveCurrentUser(
    payload: DeleteUserReq,
    response: Response,
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    security: Annotated[SecurityHandler, Depends(securityHandler)],
    userRepository: Annotated[
        UserAccountRepository,
        Depends(userAccountRepositoryHandler),
    ],
    historyRepository: Annotated[
        UserAccountHistoryRepository,
        Depends(userAccountHistoryRepositoryHandler),
    ],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
):
    async with database.transaction(session):
        user = await userRepository.getUserById(accessToken.sub)

        if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled or does not exist anymore.",
            )

        passwordMatch = security.verifyPassword(
            hashedPassword=user.password,
            plainPassword=payload.password,
        )

        if not passwordMatch:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to delete this user. Provide the correct password.",
            )

        await userRepository.updateUserStatus(
            accountStatus=UserAccountStatus.ARCHIVED,
            user=user,
            updatedAt=nowUtc,
        )

        await historyRepository.createHistoryEntry(
            userAccountId=user.id,
            statusChangedTo=UserAccountStatus.ARCHIVED,
            changedBy=user.id,
            reason="User self-initiated account closure.",
            changedAt=nowUtc,
        )

        await refreshTokenRepository.revokeUserSessions(
            userAccountId=user.id,
            rotatedAt=nowUtc,
        )

    security.revokeRefreshToken(response)

    return {"msg": "Your account profile has been successfully archived."}


@router.patch(
    "/me/password",
    response_model=MessageResp,
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="resetCurrentUserPassword",
)
async def resetCurrentUserPassword(
    payload: ResetPasswdReq,
    response: Response,
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    security: Annotated[SecurityHandler, Depends(securityHandler)],
    userRepository: Annotated[
        UserAccountRepository,
        Depends(userAccountRepositoryHandler),
    ],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
):
    async with database.transaction(session):
        user = await userRepository.getUserById(accessToken.sub)

        if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled or does not exist anymore.",
            )

        passwordMatch = security.verifyPassword(
            hashedPassword=user.password,
            plainPassword=payload.oldPasswd,
        )

        if not passwordMatch:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to update the password with a new one.",
            )

        await userRepository.updateUserPassword(
            user=user,
            hashedPassword=security.hashPassword(payload.newPasswd),
            updatedAt=nowUtc,
        )

        await refreshTokenRepository.revokeUserSessions(
            userAccountId=user.id,
            rotatedAt=nowUtc,
        )

    security.revokeRefreshToken(response)

    return {"msg": "The password was successfully updated. Please sign in again."}


@router.get(
    "/me/sessions",
    response_model=PaginatedRefreshTokenResp,
    status_code=status.HTTP_200_OK,
    operation_id="listCurrentUserSessions",
)
async def listCurrentUserSessions(
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
    onlyActive: Annotated[bool, Query(alias="active")] = True,
    allSessions: Annotated[bool, Query(alias="all")] = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, sessions = await refreshTokenRepository.listUserSessions(
        userAccountId=accessToken.sub,
        onlyActive=onlyActive,
        allSessions=allSessions,
        limit=limit,
        offset=offset,
    )

    return PaginatedRefreshTokenResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": sessions,
        }
    )


@router.get(
    "/me/sessions/{sessionId}",
    response_model=RefreshTokenResp,
    status_code=status.HTTP_200_OK,
    operation_id="getCurrentUserSession",
)
async def getCurrentUserSession(
    sessionId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
):
    session = await refreshTokenRepository.getUserSessionById(
        userAccountId=accessToken.sub,
        sessionId=sessionId,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested session could not be found.",
        )

    return session


@router.delete(
    "/me/sessions/{sessionId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="revokeCurrentUserSession",
)
async def revokeCurrentUserSession(
    sessionId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
):
    async with database.transaction(session):
        affectedRows = await refreshTokenRepository.revokeUserSessions(
            userAccountId=accessToken.sub,
            sessionId=sessionId,
            rotatedAt=nowUtc,
        )

    if affectedRows == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested session could not be found.",
        )

    return {"msg": "Session successfully revoked."}


@router.delete(
    "/me/sessions",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="revokeAllCurrentUserSessions",
)
async def revokeAllCurrentUserSessions(
    response: Response,
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    security: Annotated[SecurityHandler, Depends(securityHandler)],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
):
    async with database.transaction(session):
        await refreshTokenRepository.revokeAllActiveUserSessions(
            userAccountId=accessToken.sub,
            rotatedAt=nowUtc,
        )

    security.revokeRefreshToken(response)

    return {"msg": "All active sessions successfully terminated."}


@router.get(
    "/me/login-attempts",
    response_model=PaginatedLoginAttemptResp,
    status_code=status.HTTP_200_OK,
    operation_id="listCurrentUserLoginAttempts",
)
async def listCurrentUserLoginAttempts(
    accessToken: Annotated[AccessTokenPayload, Depends(accessHandler)],
    userRepository: Annotated[
        UserAccountRepository,
        Depends(userAccountRepositoryHandler),
    ],
    loginAttemptRepository: Annotated[
        LoginAttemptRepository,
        Depends(loginAttemptRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    userIdentity = await userRepository.getUserEmailAndUsernameById(
        accessToken.sub,
    )

    if userIdentity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found.",
        )

    email, username = userIdentity

    (
        totalRecords,
        attempts,
    ) = await loginAttemptRepository.listLoginAttemptsByUserIdentity(
        username=username,
        email=email,
        limit=limit,
        offset=offset,
    )

    return PaginatedLoginAttemptResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": attempts,
        }
    )
