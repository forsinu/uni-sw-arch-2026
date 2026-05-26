from datetime import datetime
from typing import Annotated, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status, Query

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.schema.user import (
    DeleteUserReq,
    PaginatedLoginAttemptResp,
    PaginatedRefreshTokenResp,
    RefreshTokenResp,
    UserAccountResp,
    ResetPasswdReq,
)
from src.db.models.refresh_token import RefreshToken
from src.db.models.login_attempt import LoginAttempt
from src.db.models.user_account import (
    UserAccount,
    UserAccountHistory,
    UserAccountStatus,
)

from src.core.util import handleDbOp
from src.core.security import AccessTokenPayload, SecurityHandler
from src.api.dependencies import accessHandler, dbHandler, secHandler, timeHandler


router = APIRouter()


@router.get("/me", response_model=UserAccountResp, status_code=status.HTTP_200_OK)
async def userInfo(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
):
    query = select(UserAccount).where(
        UserAccount.id == at.sub,
        UserAccount.accountStatus == UserAccountStatus.ACTIVE,
    )

    async with handleDbOp(
        session=db, errorMsg="Internal Server Error fetching profile."
    ):
        result = await db.execute(query)
        user = result.scalar_one_or_none()

    # A user could possess a valid token for a deactivated account!
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found or account is no longer active.",
        )

    return user


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
async def deleteUser(
    # request: Request,
    payload: DeleteUserReq,
    response: Response,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
):

    query = select(UserAccount).where(UserAccount.id == at.sub)

    async with handleDbOp(session=db):
        result = await db.execute(query)
        user = result.scalar_one_or_none()

    if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or does not exist anymore.",
        )

    passwdMatch = sec.verifyPassword(hash=user.password, plain=payload.password)

    if not passwdMatch:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to delete this user! Provide the right password.",
        )

    historyLog = UserAccountHistory(
        userAccountId=user.id,
        statusChangedTo=UserAccountStatus.ARCHIVED,
        changedBy=user.id,
        reason="User self-initiated automated account closure sequence.",
    )

    async with handleDbOp(session=db):
        user.accountStatus = UserAccountStatus.ARCHIVED

        db.add(historyLog)

        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.userAccountId == user.id,
                RefreshToken.isActive == True,
            )
            .values(isActive=False, rotatedAt=nowUtc)
        )

        await db.commit()

    sec.revokeRefreshToken(response)

    return {
        "msg": "Your account profile has been successfully deactivated and archived."
    }


@router.get(
    "/sessions",
    response_model=PaginatedRefreshTokenResp,
    status_code=status.HTTP_200_OK,
)
async def getUserSessions(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
    all: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    countQuery = (
        select(func.count())
        .select_from(RefreshToken)
        .where(RefreshToken.userAccountId == at.sub)
    )

    query = select(RefreshToken).where(RefreshToken.userAccountId == at.sub)

    if not all:
        countQuery = countQuery.where(RefreshToken.isActive == True)
        query = query.where(RefreshToken.isActive == True)

    query = query.order_by(RefreshToken.createdAt.desc()).offset(offset).limit(limit)

    async with handleDbOp(session=db):
        totalCount = (await db.execute(countQuery)).scalar_one()
        sessions = (await db.execute(query)).scalars().all()

    return PaginatedRefreshTokenResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalCount,
            },
            "results": sessions,
        }
    )


@router.get(
    "/sessions/{id}",
    response_model=RefreshTokenResp,
    status_code=status.HTTP_200_OK,
)
async def getUserSession(
    # request: Request,
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
):
    query = select(RefreshToken).where(
        RefreshToken.userAccountId == at.sub,
        RefreshToken.id == id,
    )

    async with handleDbOp(session=db):
        result = await db.execute(query)
        session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested session could not be found.",
        )

    return session


@router.patch(
    "/sessions/revoke",
    status_code=status.HTTP_200_OK,
)
async def revokeSessions(
    # request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    sessionId: Annotated[Optional[uuid.UUID], Query()] = None,
):
    if sessionId:
        query = update(RefreshToken).where(
            RefreshToken.userAccountId == at.sub,
            RefreshToken.id == sessionId,
        )

    else:
        query = update(RefreshToken).where(
            RefreshToken.userAccountId == at.sub,
            RefreshToken.isActive == True,
        )

    query = query.values(
        isActive=False,
        rotatedAt=nowUtc,
    )

    async with handleDbOp(session=db):
        await db.execute(query)
        await db.commit()

    if not sessionId:
        sec.revokeRefreshToken(response)

    if sessionId:
        return {"msg": "Session successufully revoked."}

    return {"msg": "All active sessions successfully terminated."}


@router.patch("/me/reset-passwd", status_code=status.HTTP_202_ACCEPTED)
async def resetPassword(
    # request: Request,
    payload: ResetPasswdReq,
    response: Response,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
):
    query = select(UserAccount).where(UserAccount.id == at.sub)

    async with handleDbOp(session=db):
        result = await db.execute(query)
        user = result.scalar_one_or_none()

    if not (user and user.accountStatus == UserAccountStatus.ACTIVE):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or does not exist anymore.",
        )

    passwdMatch = sec.verifyPassword(
        hash=user.password,
        plain=payload.oldPasswd,
    )

    if not passwdMatch:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to update the password with a new one.",
        )

    query = (
        update(RefreshToken)
        .where(
            RefreshToken.userAccountId == at.sub,
            RefreshToken.isActive == True,
        )
        .values(isActive=False, rotatedAt=nowUtc)
    )
    async with handleDbOp(session=db):
        user.password = sec.hashPassword(payload.newPasswd)

        await db.execute(query)
        await db.commit()

    sec.revokeRefreshToken(response)

    return {"msg": "The user password was successfully upgraded. Please sign in."}


@router.get(
    "/me/login-attempts",
    response_model=PaginatedLoginAttemptResp,
    status_code=status.HTTP_200_OK,
)
async def getUserLoginAttempts(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessHandler)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):

    emailQuery = select(UserAccount.email).where(UserAccount.id == at.sub)
    async with handleDbOp(session=db):
        emailResult = await db.execute(emailQuery)
        email = emailResult.scalar_one_or_none()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User email context not found!",
        )

    countQuery = (
        select(func.count())
        .select_from(LoginAttempt)
        .where(LoginAttempt.usedEmail == email)
    )
    dataQuery = (
        select(LoginAttempt)
        .where(LoginAttempt.usedEmail == email)
        .order_by(LoginAttempt.attemptedAt.desc())
        .offset(offset)
        .limit(limit)
    )

    async with handleDbOp(session=db):
        totalCount = (await db.execute(countQuery)).scalar_one()
        attempts = (await db.execute(dataQuery)).scalars().all()

    return PaginatedLoginAttemptResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalCount,
            },
            "results": attempts,
        }
    )
