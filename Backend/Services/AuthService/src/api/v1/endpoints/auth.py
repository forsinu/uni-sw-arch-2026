from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, status, Depends

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


from src.db.models.refresh_token import RefreshToken
from src.db.models.login_attempt import LoginAttempt
from src.db.models.user_account import (
    UserAccount,
    UserAccountHistory,
    UserAccountStatus,
)

from src.schema.auth import AccessTokenResp, RegisterOrLoginReq
from src.core.security import SecurityHandler
from src.core.util import ClientInfo, handleDbOp
from src.api.dependencies import (
    clientInfoHandler,
    dbHandler,
    refreshHandler,
    secHandler,
)


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
# @limiter.limit("2/minute", key_func=get_remote_address)
async def registerUser(
    # request: Request,
    cred: RegisterOrLoginReq,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):

    user = UserAccount(
        email=cred.email,
        password=sec.hashPassword(cred.password),
        accountStatus=UserAccountStatus.ACTIVE,
    )

    async with handleDbOp(
        session=db,
        integrityMsg="This email address is already registered to an account.",
    ):
        db.add(user)
        await db.flush()

        historyLog = UserAccountHistory(
            userAccountId=user.id,
            statusChangedTo=UserAccountStatus.ACTIVE,
            changedBy=user.id,
            reason="Initial registration complete. Operational account profile activated.",
        )

        db.add(historyLog)
        await db.commit()

    return {"msg": "The user was registered successfully."}


@router.post(
    "/login",
    response_model=AccessTokenResp,
    status_code=status.HTTP_200_OK,
)
# @limiter.limit("1/minute", key_func=rateLimitLogin)
async def loginUser(
    # request: Request,
    response: Response,
    cred: RegisterOrLoginReq,
    ci: Annotated[ClientInfo, Depends(clientInfoHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):

    loginAttempt = LoginAttempt(
        usedEmail=cred.email,
        ipAddress=ci.ip,
        userAgent=ci.ua,
        wasSuccessfull=False,
    )

    async with handleDbOp(session=db):
        query = await db.execute(
            select(UserAccount).where(
                UserAccount.email == cred.email,
            )
        )

        user = query.scalar_one_or_none()

        if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
            passwdMatch = False

            sec.verifyPassword(
                "$argon2id$v=19$m=65536,t=3,p=4$dHVtbXlkdW1teWR1bW15$dummyhash",
                cred.password,
            )

        else:
            passwdMatch = sec.verifyPassword(user.password, cred.password)

        if not passwdMatch:
            db.add(loginAttempt)
            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect email or password",
            )

        loginAttempt.wasSuccessfull = True
        nowUtc = datetime.now(timezone.utc)

        query = await db.execute(
            select(RefreshToken)
            .where(
                RefreshToken.userAccountId == user.id,
                RefreshToken.isActive == True,
            )
            .order_by(RefreshToken.createdAt.asc())
        )

        activeSessions = query.scalars().all()

        # Check the limit of sessions per user, if the
        # limit is exceeded, invalidate the oldest sessions
        if sec.env.MAX_SESSIONS <= len(activeSessions):
            excess = (len(activeSessions) - sec.env.MAX_SESSIONS) + 1

            sessionIds = [activeSessions[i].id for i in range(excess)]

            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.id.in_(sessionIds))
                .values(
                    isActive=False,
                    rotatedAt=nowUtc,
                )
            )

        accessToken = sec.generateAccessToken(
            nowUtc=nowUtc,
            userId=user.id,
            role=user.userRole,
            fed=user.federationId,
        )

        rt = sec.generateRandomToken(nowUtc=nowUtc)
        refreshToken = RefreshToken(
            token=rt.token,
            userAccountId=user.id,
            expiresAt=rt.exp,
            ipAddress=ci.ip,
            userAgent=ci.ua,
            isActive=True,
        )

        db.add(loginAttempt)
        db.add(refreshToken)

        await db.commit()

    sec.setRefreshToken(response=response, token=rt.token)

    return AccessTokenResp(accessToken=accessToken, tt="bearer")


# This route is used when the Access Token expires. Provide a valid
# Refresh Token to obtain a new Access Token, otherwise login again.
@router.get("/refresh", response_model=AccessTokenResp, status_code=status.HTTP_200_OK)
async def refreshToken(
    # request: Request,
    response: Response,
    rt: Annotated[RefreshToken, Depends(refreshHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    ci: Annotated[ClientInfo, Depends(clientInfoHandler)],
):

    nowUtc = datetime.now(timezone.utc)

    async with handleDbOp(session=db):
        query = await db.execute(
            select(UserAccount).where(UserAccount.id == rt.userAccountId)
        )

        user = query.scalar_one_or_none()

    if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
        sec.revokeRefreshToken(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to generate a token for this account.",
        )

    token = sec.generateRandomToken(nowUtc=nowUtc)
    refreshToken = RefreshToken(
        token=token.token,
        userAccountId=user.id,
        expiresAt=token.exp,
        ipAddress=ci.ip,
        userAgent=ci.ua,
        isActive=True,
    )

    rt.isActive = False
    rt.rotatedAt = nowUtc

    async with handleDbOp(session=db):
        db.add(refreshToken)
        await db.commit()

    at = sec.generateAccessToken(
        nowUtc=nowUtc,
        userId=user.id,
        role=user.userRole,
        fed=user.federationId,
    )

    sec.setRefreshToken(response=response, token=token.token)

    return AccessTokenResp(accessToken=at, tt="bearer")
