from datetime import datetime
from typing import Annotated, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models.user_account import UserAccountRole, UserAccountStatus


class UserCreationAdminReq(BaseModel):
    email: EmailStr
    fedId: Optional[str] = None


class RevokeUserSessionsReq(BaseModel):
    id: uuid.UUID


class UpdateUserStatusReq(BaseModel):
    status: UserAccountStatus
    reason: Annotated[str, Field(min_length=5, max_length=500)]


class PaginationMetadata(BaseModel):
    totalRecords: int
    limit: int
    offset: int
    hasMore: bool


class UserAccountAdminResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    email: EmailStr

    userRole: UserAccountRole
    federationId: Optional[str] = None

    accountStatus: UserAccountStatus

    createdAt: datetime
    updatedAt: Optional[datetime] = None

    # createdBy: Optional[uuid.UUID] = None
    # updatedBy: Optional[uuid.UUID] = None


class PaginatedUsersAdminResp(BaseModel):
    metadata: PaginationMetadata
    results: list[UserAccountAdminResp]


class RefreshTokenAdminResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID

    createdAt: datetime
    expiresAt: datetime
    rotatedAt: Optional[datetime] = None

    isActive: bool

    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None


class PaginatedRefreshTokenAdminResp(BaseModel):
    metadata: PaginationMetadata
    results: list[RefreshTokenAdminResp]


class LoginAttemptAdminResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None

    attemptedAt: datetime

    wasSuccessfull: bool


class PaginatedLoginAttemptAdminResp(BaseModel):
    metadata: PaginationMetadata
    results: list[LoginAttemptAdminResp]


class UserAccountHistoryAdminResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    statusChangedTo: UserAccountStatus

    changedAt: datetime

    changedBy: Optional[uuid.UUID]

    reason: Optional[str]


class PaginatedUserAccountHistoryAdminResp(BaseModel):
    metadata: PaginationMetadata
    results: list[UserAccountAdminResp]
