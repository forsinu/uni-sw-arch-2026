# src/api/v1/auth.py

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security.models import RefreshTokenPayload
from src.api.dependencies import (
    clientInfoHandler,
    databaseHandler,
    dbSessionHandler,
    loginAttemptRepositoryHandler,
    refreshCookieHandler,
    refreshTokenRepositoryHandler,
    securityHandler,
    timeHandler,
    userAccountHistoryRepositoryHandler,
    userAccountRepositoryHandler,
)
from src.core.sec import SecurityHandler
from src.db.errors import DbConflictError
from src.db.models.refresh_token import RefreshToken
from src.db.models.user_account import UserAccountStatus
from src.db.repositories import (
    LoginAttemptRepository,
    RefreshTokenRepository,
    UserAccountHistoryRepository,
    UserAccountRepository,
)
from src.db.session import DatabaseHandler
from src.schemas.auth import AccessTokenResp, RegisterOrLoginReq
from src.schemas.common import ClientInfo, MessageResp


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


DUMMY_ARGON2_HASH = "$argon2id$v=19$m=65536,t=3,p=4$dHVtbXlkdW1teWR1bW15$dummyhash"


@router.post(
    "/register",
    response_model=MessageResp,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerUser",
)
async def registerUser(
    credentials: RegisterOrLoginReq,
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
    try:
        async with database.transaction(session):
            user = await userRepository.createUser(
                email=credentials.email,
                hashedPassword=security.hashPassword(credentials.password),
                accountStatus=UserAccountStatus.ACTIVE,
            )

            await historyRepository.createHistoryEntry(
                userAccountId=user.id,
                statusChangedTo=UserAccountStatus.ACTIVE,
                changedBy=user.id,
                reason="Initial registration complete. Operational account profile activated.",
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already registered to an account.",
        ) from exc

    return {"msg": "The user was registered successfully."}


@router.post(
    "/login",
    response_model=AccessTokenResp,
    status_code=status.HTTP_200_OK,
    operation_id="loginUser",
)
async def loginUser(
    response: Response,
    credentials: RegisterOrLoginReq,
    clientInfo: Annotated[ClientInfo, Depends(clientInfoHandler)],
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
    loginAttemptRepository: Annotated[
        LoginAttemptRepository,
        Depends(loginAttemptRepositoryHandler),
    ],
):
    loginFailed = False
    accessToken = None
    refreshTokenValue = None

    async with database.transaction(session):
        user = await userRepository.getUserByEmail(credentials.email)

        if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
            loginFailed = True

            # Timing side-channel mitigation.
            security.verifyPassword(
                hashedPassword=DUMMY_ARGON2_HASH,
                plainPassword=credentials.password,
            )

        else:
            passwordMatch = security.verifyPassword(
                hashedPassword=user.password,
                plainPassword=credentials.password,
            )

            if not passwordMatch:
                loginFailed = True

        if loginFailed:
            await loginAttemptRepository.createLoginAttempt(
                usedEmail=credentials.email,
                ipAddress=clientInfo.ip,
                userAgent=clientInfo.ua,
                wasSuccessful=False,
            )

        else:
            await loginAttemptRepository.createLoginAttempt(
                usedEmail=credentials.email,
                ipAddress=clientInfo.ip,
                userAgent=clientInfo.ua,
                wasSuccessful=True,
            )

            await refreshTokenRepository.revokeOldestSessionsIfLimitExceeded(
                userAccountId=user.id,
                maxSessions=security.env.MAX_SESSIONS,
                rotatedAt=nowUtc,
            )

            refreshPayload: RefreshTokenPayload = security.generateRefreshToken(
                nowUtc=nowUtc
            )

            await refreshTokenRepository.createRefreshToken(
                token=refreshPayload.token,
                userAccountId=user.id,
                expiresAt=refreshPayload.exp,
                ipAddress=clientInfo.ip,
                userAgent=clientInfo.ua,
            )

            refreshTokenValue = refreshPayload.token

            accessToken = security.generateAccessToken(
                nowUtc=nowUtc,
                userId=user.id,
                role=user.userRole,
                fed=user.federationId,
            )

    if loginFailed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password.",
        )

    security.setRefreshToken(
        response=response,
        token=refreshTokenValue,
    )

    return AccessTokenResp(
        accessToken=accessToken,
        tt="bearer",
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResp,
    status_code=status.HTTP_200_OK,
    operation_id="refreshAccessToken",
)
async def refreshAccessToken(
    response: Response,
    refreshTokenValueFromCookie: Annotated[str, Depends(refreshCookieHandler)],
    clientInfo: Annotated[ClientInfo, Depends(clientInfoHandler)],
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
    accessToken = None
    newRefreshTokenValue = None
    mustRevokeCookie = False
    unauthorizedDetail = None

    async with database.transaction(session):
        dbRefreshToken = await refreshTokenRepository.getRefreshTokenByToken(
            refreshTokenValueFromCookie
        )

        if dbRefreshToken is None:
            mustRevokeCookie = True
            unauthorizedDetail = "Invalid session. Please sign in again."

        elif not dbRefreshToken.isActive:
            mustRevokeCookie = True
            unauthorizedDetail = "Invalid session. Please sign in again."

            await refreshTokenRepository.revokeUserSessions(
                userAccountId=dbRefreshToken.userAccountId,
                rotatedAt=nowUtc,
            )

        else:
            expiresAt = refreshTokenRepository.normalizeExpiresAt(dbRefreshToken)

            if nowUtc >= expiresAt:
                mustRevokeCookie = True
                unauthorizedDetail = "Session expired. Please sign in again."

                await refreshTokenRepository.revokeUserSessions(
                    token=dbRefreshToken.token,
                    userAccountId=dbRefreshToken.userAccountId,
                    rotatedAt=nowUtc,
                )

            else:
                user = await userRepository.getUserById(
                    userId=dbRefreshToken.userAccountId,
                    isActive=True,
                )

                if user is None:
                    mustRevokeCookie = True
                    unauthorizedDetail = "Unable to generate a token for this account."

                    await refreshTokenRepository.revokeUserSessions(
                        token=dbRefreshToken.token,
                        userAccountId=dbRefreshToken.userAccountId,
                        rotatedAt=nowUtc,
                    )

                else:
                    await refreshTokenRepository.revokeUserSessions(
                        token=dbRefreshToken.token,
                        rotatedAt=nowUtc,
                    )

                    newRefreshPayload = security.generateRefreshToken(nowUtc=nowUtc)

                    await refreshTokenRepository.createRefreshToken(
                        token=newRefreshPayload.token,
                        userAccountId=user.id,
                        expiresAt=newRefreshPayload.exp,
                        ipAddress=clientInfo.ip,
                        userAgent=clientInfo.ua,
                    )

                    newRefreshTokenValue = newRefreshPayload.token

                    accessToken = security.generateAccessToken(
                        nowUtc=nowUtc,
                        userId=user.id,
                        role=user.userRole,
                        fed=user.federationId,
                    )

    if mustRevokeCookie:
        security.revokeRefreshToken(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=unauthorizedDetail,
        )

    security.setRefreshToken(
        response=response,
        token=newRefreshTokenValue,
    )

    return AccessTokenResp(
        accessToken=accessToken,
        tt="bearer",
    )


@router.post(
    "/logout",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="logoutCurrentSession",
)
async def logoutCurrentSession(
    response: Response,
    refreshToken: Annotated[str, Depends(refreshCookieHandler)],
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
        await refreshTokenRepository.revokeUserSessions(
            token=refreshToken,
            rotatedAt=nowUtc,
        )

    security.revokeRefreshToken(response)

    return {"msg": "Current session successfully terminated."}
