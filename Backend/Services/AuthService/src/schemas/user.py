# src/schema/user.py

from datetime import datetime
import uuid

from pydantic import AliasChoices, Field

from src.db.models.user_account import UserAccountRole, UserAccountStatus
from src.schemas.common import BaseSchema, PaginatedResp


class DeleteUserReq(BaseSchema):
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class ResetPasswdReq(BaseSchema):
    oldPasswd: str = Field(
        min_length=8,
        max_length=128,
    )

    newPasswd: str = Field(
        min_length=8,
        max_length=128,
    )


class UserAccountResp(BaseSchema):
    id: uuid.UUID
    email: str
    userRole: UserAccountRole
    federationId: str | None = None
    accountStatus: UserAccountStatus
    createdAt: datetime
    updatedAt: datetime | None = None


class RefreshTokenResp(BaseSchema):
    id: uuid.UUID
    userAccountId: uuid.UUID
    createdAt: datetime
    expiresAt: datetime
    rotatedAt: datetime | None = None
    isActive: bool
    ipAddress: str | None = None
    userAgent: str | None = None


class LoginAttemptResp(BaseSchema):
    id: uuid.UUID
    usedEmail: str
    ipAddress: str | None = None
    userAgent: str | None = None
    attemptedAt: datetime

    # Supports both the corrected model field `wasSuccessful`
    # and the previous typo `wasSuccessfull`.
    wasSuccessful: bool = Field(
        validation_alias=AliasChoices(
            "wasSuccessful",
            "wasSuccessfull",
        )
    )


class PaginatedRefreshTokenResp(PaginatedResp[RefreshTokenResp]):
    pass


class PaginatedLoginAttemptResp(PaginatedResp[LoginAttemptResp]):
    pass
