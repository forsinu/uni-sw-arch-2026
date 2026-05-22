from datetime import datetime, timezone
from typing import Annotated
import uuid
from fastapi import APIRouter, HTTPException, Response, status, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import accessHandler, dbHandler, secHandler
from src.core.security import SecurityHandler
from src.core.util import handleDbOp
from src.db.model import RefreshToken, ResetPasswdAttempt, UserAccount
from src.schema.user import RefreshTokenResp, ResetPasswdReq, UserAccountResp

router = APIRouter()


@router.get("/me", response_model=UserAccountResp, status_code=status.HTTP_200_OK)
async def getUserInfo(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessHandler)],
):
    async with handleDbOp(db, "Internal Server Error"):
        query = (
            select(UserAccount)
            .where(UserAccount.id == at.sub)
            .options(selectinload(UserAccount.refreshTokens))
        )

        result = await db.execute(query)

        userAccount = result.scalar_one_or_none()

    if not userAccount:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account is disabled or does not exist anymore.",
        )

    return userAccount


@router.get(
    "/sessions", response_model=list[RefreshTokenResp], status_code=status.HTTP_200_OK
)
async def getActiveSessions(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessHandler)],
):
    async with handleDbOp(db, "Internal Server Error"):
        query = (
            select(RefreshToken)
            .where(RefreshToken.userAccountId == at.sub, RefreshToken.isActive)
            .order_by(RefreshToken.createdAt)
        )

        result = await db.execute(query)

        activeSessions = result.scalars().all()

    return activeSessions


@router.patch("/sessions/revokes", status_code=status.HTTP_200_OK)
async def revokeAllSessions(
    response: Response,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessHandler)],
    sec: Annotated[SecurityHandler, Depends(dbHandler)],
):
    async with handleDbOp(db, "Internal Server Error"):
        query = (
            update(RefreshToken)
            .where(RefreshToken.userAccountId == at.sub, RefreshToken.isActive)
            .values(
                isActive=False,
                rotatedAt=datetime.now(timezone.utc),
            )
        )

        await db.execute(query)
        await db.commit()

    sec.revokeRefreshToken(response)

    return {"msg": "All active sessions successfully terminated."}


@router.patch("/sessions/{tokenId}/revoke", status_code=status.HTTP_200_OK)
async def revokeToken(
    tokenId: uuid.UUID,
    response: Response,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessHandler)],
):

    async with handleDbOp(db, "Internal Server Error"):
        query = (
            update(RefreshToken)
            .where(
                RefreshToken.userAccountId == at.sub,
                RefreshToken.id == tokenId,
                RefreshToken.isActive,
            )
            .values(
                isActive=False,
                rotatedAt=datetime.now(timezone.utc),
            )
        )

        await db.execute(query)
        await db.commit()

        # if result.rowcount == 0:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Target active session record not found.",
        #     )

    return {"detail": "Target session successfully terminated."}


@router.patch("/reset-passwd", status_code=status.HTTP_200_OK)
async def resetPassword(
    passwdReq: ResetPasswdReq,
    response: Response,
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    db: Annotated[AsyncSession, Depends(dbHandler)],
    at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessHandler)],
):

    await sec.checkRateLimit(
        db=db,
        model=ResetPasswdAttempt,
        emailOrIdColumn=ResetPasswdAttempt.userAccountId,
        targetValue=at.sub,
    )

    attemptLog = ResetPasswdAttempt(userAccountId=at.sub)

    async with handleDbOp(db, "Internal Server Error"):
        query = await db.execute(select(UserAccount).where(UserAccount.id == at.sub))

        result = query.scalar_one_or_none()

    if not result or not result.isActive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or user account has been disabled.",
        )

    if not sec.verifyPassword(
        hash=result.password,
        plain=passwdReq.oldPasswd,
    ) or not (passwdReq.oldPasswd != passwdReq.newPasswd):
        async with handleDbOp(db, "Internal Server Error"):
            db.add(attemptLog)

            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password provided.",
        )

    hashedNewPasswd = sec.hashPassword(password=passwdReq.newPasswd)
    attemptLog.wasSuccessfull = True

    async with handleDbOp(db, "Internal Server Error"):
        db.add(attemptLog)
        await db.execute(
            update(UserAccount)
            .where(UserAccount.id == at.sub)
            .values(password=hashedNewPasswd)
        )

        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.userAccountId == at.sub,
                RefreshToken.isActive == True,
            )
            .values(
                isActive=False,
                rotatedAt=datetime.now(timezone.utc),
            )
        )

        await db.commit()

    sec.revokeRefreshToken(response=response)

    return {"msg": "The password reset was successful. Please sign in again."}
