from datetime import datetime
from typing import Annotated, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class UserAssociationReq(BaseModel):
    federationId: Annotated[str, Field(max_length=32)]
    # userId: uuid.UUID

    email: EmailStr
    password: Annotated[str, Field(min_length=12, max_length=64)]


class RefreshTokenSubResp(BaseModel):
    token: str

    createdAt: datetime
    expiresAt: datetime
    rotatedAt: Optional[datetime]

    isActive: bool

    ipAddress: str
    userAgent: str

    class Config:
        from_attributes = True


class UsersAdminResp(BaseModel):
    id: uuid.UUID
    email: EmailStr

    isActive: bool

    disabledAt: Optional[datetime]
    createdAt: datetime
    updatedAt: Optional[datetime]

    createdBy: Optional[uuid.UUID]
    updatedBy: Optional[uuid.UUID]

    refreshTokens: list[RefreshTokenSubResp]

    class Config:
        from_attributes = True
