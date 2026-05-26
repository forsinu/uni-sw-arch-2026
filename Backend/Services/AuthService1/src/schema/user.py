from datetime import datetime
from typing import Annotated, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models.user_account import UserAccountRole


class DeleteUserReq(BaseModel):
    password: str


class ResetPasswdReq(BaseModel):
    oldPasswd: Annotated[str, Field(..., max_length=64)]
    newPasswd: Annotated[
        str,
        Field(
            ...,
            min_length=12,
            max_length=64,
        ),
    ]


class PaginationMetadata(BaseModel):
    totalRecords: int
    limit: int
    offset: int
    hasMore: bool


class LoginAttemptsResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None

    attemptedAt: datetime

    wasSuccessfull: bool


class PaginatedLoginAttemptResp(BaseModel):
    metadata: PaginationMetadata
    results: list[LoginAttemptsResp]


class RefreshTokenResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    createdAt: datetime
    expiresAt: datetime
    rotatedAt: Optional[datetime] = None

    isActive: bool

    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None


class PaginatedRefreshTokenResp(BaseModel):
    metadata: PaginationMetadata
    results: list[RefreshTokenResp]


class UserAccountResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    email: EmailStr

    userRole: UserAccountRole
    federationId: Optional[str] = None

    createdAt: datetime
    updatedAt: Optional[datetime] = None
