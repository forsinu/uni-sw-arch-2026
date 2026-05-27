from datetime import datetime
from typing import Annotated, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.login_attempt import LoginAttempt
from src.db.models.refresh_token import RefreshToken
from src.db.models.user_account import (
    UserAccount,
    UserAccountHistory,
    UserAccountRole,
    UserAccountStatus,
)
from src.api.dependencies import accessAdminHandler, dbHandler, secHandler, timeHandler
from src.core.security import AccessTokenPayload, SecurityHandler
from src.schema.admin import (
    PaginatedLoginAttemptAdminResp,
    PaginatedRefreshTokenAdminResp,
    PaginatedUserAccountHistoryAdminResp,
    UpdateUserStatusReq,
    UserAccountAdminResp,
    PaginatedUsersAdminResp,
    UserCreationAdminReq,
)
from src.core.util import handleDbOp


router = APIRouter()


@router.get(
    "/users",
    response_model=PaginatedUsersAdminResp,
    status_code=status.HTTP_200_OK,
)
async def getUsersAdmin(
    # at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    countQuery = select(func.count()).select_from(UserAccount)
    dataQuery = (
        select(UserAccount)
        .order_by(UserAccount.createdAt.desc())
        .offset(offset)
        .limit(limit)
    )

    async with handleDbOp(session=db):
        countResult = await db.execute(countQuery)
        totalCount = countResult.scalar_one()

        dataResult = await db.execute(dataQuery)
        users = dataResult.scalars().all()

    return PaginatedUsersAdminResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalCount,
            },
            "results": users,
        }
    )


@router.get(
    "/users/{id}",
    response_model=UserAccountAdminResp,
    status_code=status.HTTP_200_OK,
)
async def getUserAdminById(
    id: uuid.UUID,
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
):
    query = (
        select(UserAccount).where(UserAccount.id == id)
        # .options(selectinload(UserAccount.refreshTokens))
    )

    async with handleDbOp(session=db):
        result = await db.execute(query)
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested user profile does not exist.",
        )

    return user


@router.get(
    "/users/{id}/sessions",
    response_model=PaginatedRefreshTokenAdminResp,
    status_code=status.HTTP_200_OK,
)
async def getSessionsByUserId(
    id: uuid.UUID,
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    countQuery = (
        select(func.count())
        .select_from(RefreshToken)
        .where(RefreshToken.userAccountId == id)
    )
    dataQuery = (
        select(RefreshToken)
        .where(RefreshToken.userAccountId == id)
        .order_by(RefreshToken.createdAt.desc())
        .offset(offset)
        .limit(limit)
    )

    async with handleDbOp(session=db):
        totalCount = (await db.execute(countQuery)).scalar_one()
        tokens = (await db.execute(dataQuery)).scalars().all()

    return PaginatedRefreshTokenAdminResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalCount,
            },
            "results": tokens,
        }
    )


@router.patch(
    "/users/{userId}/sessions/revoke",
    status_code=status.HTTP_200_OK,
)
async def revokeUserSessions(
    userId: uuid.UUID,
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
    sessionId: Annotated[Optional[uuid.UUID], Query()] = None,
):
    query = update(RefreshToken).where(RefreshToken.userAccountId == userId)

    if sessionId:
        query = query.where(RefreshToken.id == sessionId)
        successMsg = (
            f"The selected session token ({sessionId}) was successfully revoked."
        )
    else:
        successMsg = (
            "All active device sessions for this user were successfully terminated."
        )

    query = query.values(isActive=False, rotatedAt=nowUtc)

    async with handleDbOp(session=db):
        await db.execute(query)
        await db.commit()

    return {"msg": successMsg}


@router.patch("/users/{userId}/status", status_code=status.HTTP_200_OK)
async def updateUserStatus(
    userId: uuid.UUID,
    payload: UpdateUserStatusReq,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
):
    query = select(UserAccount).where(UserAccount.id == userId)
    async with handleDbOp(session=db):
        result = await db.execute(query)
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {userId} could not be found.",
        )

    if user.accountStatus == payload.status:
        return {"msg": f"User account state is already set to {payload.status.value}."}

    userHistory = UserAccountHistory(
        userAccountId=userId,
        statusChangedTo=payload.status,
        changedBy=at.sub,
        reason=payload.reason,
    )

    sessionEvictionQuery = (
        update(RefreshToken)
        .where(
            RefreshToken.userAccountId == userId,
            RefreshToken.isActive == True,
        )
        .values(isActive=False, rotatedAt=nowUtc)
    )

    async with handleDbOp(session=db):
        user.accountStatus = payload.status
        user.updatedAt = nowUtc

        db.add(userHistory)

        await db.execute(sessionEvictionQuery)
        await db.commit()

    return {
        "msg": f"The user account state was successfully updated to {payload.status.value}.",
        "userId": str(userId),
        "newStatus": payload.status.value,
    }


@router.get(
    "/login-attempts",
    response_model=PaginatedLoginAttemptAdminResp,
    status_code=status.HTTP_200_OK,
)
async def getLoginAttempts(
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    email: Annotated[Optional[str], Query(max_length=320)] = None,
):

    countQuery = select(func.count()).select_from(LoginAttempt)

    dataQuery = (
        select(LoginAttempt)
        .order_by(LoginAttempt.attemptedAt.desc())
        .offset(offset)
        .limit(limit)
    )

    if email:
        countQuery = countQuery.where(LoginAttempt.usedEmail == email)
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

    return PaginatedLoginAttemptAdminResp.model_validate(
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


@router.get(
    "/users/{userId}/history",
    response_model=PaginatedUserAccountHistoryAdminResp,
    status_code=status.HTTP_200_OK,
)
async def getUserHistory(
    id: uuid.UUID,
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    countQuery = (
        select(func.count())
        .select_from(UserAccountHistory)
        .where(UserAccountHistory.userAccountId == id)
    )

    dataQuery = (
        select(UserAccountHistory)
        .where(UserAccountHistory.userAccountId == id)
        .order_by(UserAccountHistory.changedAt.desc())
        .offset(offset)
        .limit(limit)
    )

    async with handleDbOp(session=db):
        totalCount = (await db.execute(countQuery)).scalar_one()
        history = (await db.execute(dataQuery)).scalars().all()

    return PaginatedLoginAttemptAdminResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalCount,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalCount,
            },
            "results": history,
        }
    )


@router.post("/users/create", status_code=status.HTTP_201_CREATED)
async def createUserAccount(
    payload: UserCreationAdminReq,
    at: Annotated[AccessTokenPayload, Depends(accessAdminHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    nowUtc: Annotated[datetime, Depends(timeHandler)],
):
    passwdGen = sec.generateRandomPassword(sec.env.PASSWORD_LEN)
    user = UserAccount(
        email=payload.email,
        password=sec.hashPassword(password=passwdGen),
        federationId=payload.fedId,
        createdAt=nowUtc,
        userRole=UserAccountRole.DEFAULT,
        accountStatus=UserAccountStatus.ACTIVE,
    )

    async with handleDbOp(
        session=db,
        integrityMsg="Duplicated Email.",
    ):
        db.add(user)
        await db.flush()

        history = UserAccountHistory(
            userAccountId=user.id,
            statusChangedTo=UserAccountStatus.ACTIVE,
            changedAt=nowUtc,
            changedBy=at.sub,
            reason="User Created!",
        )

        db.add(history)
        await db.commit()

    return {"msg": "User account successfully provisioned.", "userId": str(user.id)}
