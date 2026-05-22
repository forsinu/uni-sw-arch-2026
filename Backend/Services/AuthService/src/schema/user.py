from datetime import datetime
from typing import Annotated, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field

from src.db.model import UserAccountRole


class RefreshTokenResp(BaseModel):
    id: uuid.UUID

    createdAt: datetime
    expiresAt: datetime
    rotatedAt: Optional[datetime]

    isActive: bool

    ipAddress: str
    userAgent: str

    class Config:
        from_attributes = True


class UserAccountResp(BaseModel):
    email: EmailStr

    userRole: UserAccountRole
    federationId: Optional[uuid.UUID]

    createdAt: datetime

    updatedAt: Optional[datetime]

    refreshTokens: list[RefreshTokenResp]

    class Config:
        from_attributes = True


class ResetPasswdReq(BaseModel):
    oldPasswd: Annotated[str, Field(max_length=64)]
    newPasswd: Annotated[str, Field(min_length=12, max_length=64)]
