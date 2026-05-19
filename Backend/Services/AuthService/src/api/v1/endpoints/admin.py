from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.security import HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession

import uuid

from src.db.model import UserAccountRole
from src.core.security import SecurityHandler
from src.api.dependencies import dbHandler, secHandler, tokenHandler
from src.schema.admin import UserAssociationReq


router = APIRouter()


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
)
async def userAssociation(
    cred: UserAssociationReq,
    # === Dependencies
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    at: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
):
    pass


@router.get(
    "/users/{id}",
    status_code=status.HTTP_200_OK,
)
async def getUserById(id: uuid.UUID):
    pass


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
