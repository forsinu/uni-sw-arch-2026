# src/schema/swimming_team.py

from datetime import datetime
import uuid

from pydantic import Field

from src.schemas.common import BaseSchema, PaginatedResp


class SwimmingTeamCreateReq(BaseSchema):
    name: str = Field(min_length=2, max_length=128)
    shortName: str | None = Field(default=None, min_length=2, max_length=16)


class SwimmingTeamUpdateReq(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    shortName: str | None = Field(default=None, min_length=2, max_length=16)
    isActive: bool | None = None


class SwimmingTeamResp(BaseSchema):
    id: uuid.UUID
    name: str
    shortName: str | None = None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime | None = None


class PaginatedSwimmingTeamResp(PaginatedResp[SwimmingTeamResp]):
    pass
