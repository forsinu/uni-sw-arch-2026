from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from sqlalchemy import insert, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

import uuid

from src.core.util import handleDbOp
from src.db.model import RefreshToken, UserAccount, UserAccountRole
from src.core.security import SecurityHandler
from src.api.dependencies import accessAdminHandler, dbHandler, secHandler, tokenHandler
from src.schema.admin import UserAssociationReq, UsersAdminResp


router = APIRouter()


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
)
async def userAssociation(
    cred: UserAssociationReq,
    bg: BackgroundTasks,
    # === Dependencies
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessAdminHandler)],
):
    tmpPassword = sec.generateRandomPassword(length=sec.env.PASSWD_LENGTH)
    hashed = sec.hashPassword(tmpPassword)

    async with handleDbOp(db, "Internal Server Error"):
        await db.execute(
            insert(UserAccount).values(
                federationId=cred.federationId,
                email=cred.email,
                password=hashed,
                createdBy=at.sub,
            )
        )

        await db.commit()

    # TODO: Sent a link with the password via email! fastapi-mail
    ## bg.add_task()

    return {
        "msg": "A user account associated with a federation record was successfully created!"
    }


@router.get(
    "/users/{id}",
    response_model=UsersAdminResp,
    status_code=status.HTTP_200_OK,
)
async def getUserById(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    # Already computed in the router dependencies !!!
    # at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessAdminHandler)],
):
    async with handleDbOp(db, "Internal Server Error"):
        query = await db.execute(
            select(UserAccount)
            .where(UserAccount.id == id)
            .options(selectinload(UserAccount.refreshTokens))
        )

        searchedUser = query.scalar_one_or_none()

    if not searchedUser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity you are looking for doesn't exist!",
        )

    return searchedUser


@router.patch("users/{id}/revoke", status_code=status.HTTP_200_OK)
async def revokeUserAccount(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    # sec: Annotated[SecurityHandler, Depends(secHandler)],
    # at: Annotated[SecurityHandler.AccessTokenPayload, Depends(accessAdminHandler)],
):
    async with handleDbOp(db, "Internal Server Error"):
        query1 = (
            update(UserAccount)
            .where(UserAccount.id == id)
            .values(
                isActive=False,
                disabledAt=datetime.now(timezone.utc),
            )
        )

        await db.execute(query1)

        query2 = (
            update(RefreshToken)
            .where(
                RefreshToken.userAccountId == id,
                RefreshToken.isActive,
            )
            .values(
                isActive=False,
                rotatedAt=datetime.now(timezone.utc),
            )
        )

        await db.execute(query2)

        await db.commit()

    return {"msg": "User successfully deactivated!"}


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
)
async def getUserByParams(
    db: Annotated[AsyncSession, Depends(dbHandler)],
    # Existing Filters
    fedId: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[UserAccountRole] = None,
    dis: Annotated[
        Optional[bool], Query(description="Filter by active/disabled status")
    ] = None,
    ca: Annotated[
        Optional[datetime],
        Query(description="Filter users created after this timestamp (ISO 8601)"),
    ] = None,
    cb: Annotated[
        Optional[datetime],
        Query(description="Filter users created before this timestamp (ISO 8601)"),
    ] = None,
):
    pass
