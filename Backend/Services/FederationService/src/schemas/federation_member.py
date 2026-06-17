# src/schema/federation_member.py

from datetime import date, datetime
import uuid

from pydantic import Field

from src.db.models.federation_members import FederationRole
from src.schemas.common import BaseSchema, PaginatedResp


class FederationMemberCreateReq(BaseSchema):
    fedRole: FederationRole
    teamId: uuid.UUID | None = None

    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    birth: date | None = None

    memberCode: str | None = Field(default=None, min_length=4, max_length=64)


class FederationMemberUpdateReq(BaseSchema):
    fedRole: FederationRole | None = None
    teamId: uuid.UUID | None = None

    firstName: str | None = Field(default=None, min_length=1, max_length=100)
    lastName: str | None = Field(default=None, min_length=1, max_length=100)
    birth: date | None = None

    isActive: bool | None = None


class FederationMemberResp(BaseSchema):
    id: uuid.UUID
    federationId: str
    fedRole: FederationRole
    teamId: uuid.UUID | None = None

    memberCode: str
    firstName: str
    lastName: str
    birth: date | None = None

    isActive: bool
    createdAt: datetime
    updatedAt: datetime | None = None


class PaginatedFederationMemberResp(PaginatedResp[FederationMemberResp]):
    pass
