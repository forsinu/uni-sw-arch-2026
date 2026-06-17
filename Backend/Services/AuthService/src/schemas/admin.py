# src/schema/admin.py

from datetime import datetime
import uuid

from pydantic import Field

from src.db.models.user_account import UserAccountStatus
from src.schemas.common import BaseSchema, PaginatedResp
from src.schemas.user import (
    LoginAttemptResp,
    RefreshTokenResp,
    UserAccountResp,
)


class UserCreationAdminReq(BaseSchema):
    email: str = Field(
        min_length=3,
        max_length=320,
        examples=["new.user@example.com"],
    )

    fedId: str | None = Field(
        default=None,
        max_length=32,
        examples=["RRR-123456789"],
    )


class UpdateUserStatusReq(BaseSchema):
    status: UserAccountStatus

    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class UserAccountAdminResp(UserAccountResp):
    pass


class UserAccountHistoryAdminResp(BaseSchema):
    id: uuid.UUID
    userAccountId: uuid.UUID
    statusChangedTo: UserAccountStatus
    changedAt: datetime
    changedBy: uuid.UUID | None = None
    reason: str | None = None


class PaginatedUsersAdminResp(PaginatedResp[UserAccountAdminResp]):
    pass


class PaginatedRefreshTokenAdminResp(PaginatedResp[RefreshTokenResp]):
    pass


class PaginatedLoginAttemptAdminResp(PaginatedResp[LoginAttemptResp]):
    pass


class PaginatedUserAccountHistoryAdminResp(PaginatedResp[UserAccountHistoryAdminResp]):
    pass
