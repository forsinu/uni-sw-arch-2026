# src/api/v1/admin.py

from datetime import datetime
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    accessAdminHandler,
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
from src.db.errors import DbConflictError
from src.db.models.user_account import UserAccountRole, UserAccountStatus
from src.db.repositories import (
    LoginAttemptRepository,
    RefreshTokenRepository,
    UserAccountHistoryRepository,
    UserAccountRepository,
)
from src.db.session import DatabaseHandler
from src.schemas.admin import (
    PaginatedLoginAttemptAdminResp,
    PaginatedRefreshTokenAdminResp,
    PaginatedUserAccountHistoryAdminResp,
    PaginatedUsersAdminResp,
    UpdateUserStatusReq,
    UserAccountAdminResp,
    UserCreationAdminReq,
)


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
)


@router.get(
    "/users",
    response_model=PaginatedUsersAdminResp,
    status_code=status.HTTP_200_OK,
    operation_id="listUsersAdmin",
)
async def listUsersAdmin(
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    userRepository: Annotated[
        UserAccountRepository,
        Depends(userAccountRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, users = await userRepository.listUsers(
        limit=limit,
        offset=offset,
    )

    return PaginatedUsersAdminResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": users,
        }
    )


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    operation_id="createUserAdmin",
)
async def createUserAdmin(
    payload: UserCreationAdminReq,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
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
):
    generatedPassword = security.generateRandomPassword(security.env.PASSWORD_MIN_LEN)

    try:
        async with database.transaction(session):
            user = await userRepository.createUser(
                email=payload.email,
                username=payload.username,
                hashedPassword=security.hashPassword(generatedPassword),
                federationId=payload.fedId,
                userRole=UserAccountRole.DEFAULT,
                accountStatus=UserAccountStatus.ACTIVE,
                createdAt=nowUtc,
            )

            await historyRepository.createHistoryEntry(
                userAccountId=user.id,
                statusChangedTo=UserAccountStatus.ACTIVE,
                changedBy=accessToken.sub,
                reason="User account provisioned by administrator.",
                changedAt=nowUtc,
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicated email or federation identifier.",
        ) from exc

    return {
        "msg": "User account successfully provisioned.",
        "userId": str(user.id),
        "temporaryPassword": generatedPassword,
    }


@router.get(
    "/users/{userId}",
    response_model=UserAccountAdminResp,
    status_code=status.HTTP_200_OK,
    operation_id="getUserAdmin",
)
async def getUserAdmin(
    userId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    userRepository: Annotated[
        UserAccountRepository,
        Depends(userAccountRepositoryHandler),
    ],
):
    user = await userRepository.getUserById(userId)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested user profile does not exist.",
        )

    return user


@router.patch(
    "/users/{userId}/status",
    status_code=status.HTTP_200_OK,
    operation_id="updateUserStatusAdmin",
)
async def updateUserStatusAdmin(
    userId: uuid.UUID,
    payload: UpdateUserStatusReq,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
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
        user = await userRepository.getUserById(userId)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {userId} could not be found.",
            )

        if user.accountStatus == payload.status:
            return {
                "msg": f"User account state is already set to {payload.status.value}."
            }

        await userRepository.updateUserStatus(
            user=user,
            accountStatus=payload.status,
            updatedAt=nowUtc,
        )

        await historyRepository.createHistoryEntry(
            userAccountId=userId,
            statusChangedTo=payload.status,
            changedBy=accessToken.sub,
            reason=payload.reason,
            changedAt=nowUtc,
        )

        if payload.status != UserAccountStatus.ACTIVE:
            await refreshTokenRepository.revokeUserSessions(
                userAccountId=userId,
                rotatedAt=nowUtc,
            )

    return {
        "msg": f"The user account state was successfully updated to {payload.status.value}.",
        "userId": str(userId),
        "newStatus": payload.status.value,
    }


@router.get(
    "/users/{userId}/sessions",
    response_model=PaginatedRefreshTokenAdminResp,
    status_code=status.HTTP_200_OK,
    operation_id="listUserSessionsAdmin",
)
async def listUserSessionsAdmin(
    userId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
    includeAll: Annotated[bool, Query(alias="all")] = True,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, sessions = await refreshTokenRepository.listUserSessions(
        userAccountId=userId,
        includeAll=includeAll,
        limit=limit,
        offset=offset,
    )

    return PaginatedRefreshTokenAdminResp.model_validate(
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


@router.delete(
    "/users/{userId}/sessions/{sessionId}",
    status_code=status.HTTP_200_OK,
    operation_id="revokeUserSessionAdmin",
)
async def revokeUserSessionAdmin(
    userId: uuid.UUID,
    sessionId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
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
            userAccountId=userId,
            sessionId=sessionId,
            rotatedAt=nowUtc,
        )

    if affectedRows == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected session token could not be found.",
        )

    return {
        "msg": "The selected session token was successfully revoked.",
        "sessionId": str(sessionId),
    }


@router.delete(
    "/users/{userId}/sessions",
    status_code=status.HTTP_200_OK,
    operation_id="revokeAllUserSessionsAdmin",
)
async def revokeAllUserSessionsAdmin(
    userId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    database: Annotated[DatabaseHandler, Depends(databaseHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    refreshTokenRepository: Annotated[
        RefreshTokenRepository,
        Depends(refreshTokenRepositoryHandler),
    ],
):
    async with database.transaction(session):
        await refreshTokenRepository.revokeUserSessions(
            userAccountId=userId,
            rotatedAt=nowUtc,
        )

    return {"msg": "All active device sessions for this user were terminated."}


@router.get(
    "/users/{userId}/history",
    response_model=PaginatedUserAccountHistoryAdminResp,
    status_code=status.HTTP_200_OK,
    operation_id="listUserHistoryAdmin",
)
async def listUserHistoryAdmin(
    userId: uuid.UUID,
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    historyRepository: Annotated[
        UserAccountHistoryRepository,
        Depends(userAccountHistoryRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, history = await historyRepository.listUserHistory(
        userAccountId=userId,
        limit=limit,
        offset=offset,
    )

    return PaginatedUserAccountHistoryAdminResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": history,
        }
    )


@router.get(
    "/login-attempts",
    response_model=PaginatedLoginAttemptAdminResp,
    status_code=status.HTTP_200_OK,
    operation_id="listLoginAttemptsAdmin",
)
async def listLoginAttemptsAdmin(
    accessToken: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    loginAttemptRepository: Annotated[
        LoginAttemptRepository,
        Depends(loginAttemptRepositoryHandler),
    ],
    cred: Annotated[str | None, Query(max_length=320)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    (
        totalRecords,
        attempts,
    ) = await loginAttemptRepository.listLoginAttemptsByEmailOrUsername(
        usedEmailOrUsername=cred,
        limit=limit,
        offset=offset,
    )

    return PaginatedLoginAttemptAdminResp.model_validate(
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
