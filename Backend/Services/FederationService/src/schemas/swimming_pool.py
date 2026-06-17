# src/schema/swimming_pool.py

from datetime import datetime
import uuid

from pydantic import Field

from src.db.models.swimming_pool import PoolLength, PoolType
from src.schemas.common import BaseSchema, PaginatedResp


class SwimmingPoolCreateReq(BaseSchema):
    name: str = Field(min_length=2, max_length=128)
    poolType: PoolType
    poolLength: PoolLength
    laneCount: int = Field(ge=1, le=20)

    streetAddress: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=64)
    postalCode: str = Field(min_length=2, max_length=16)
    countryIso: str = Field(min_length=2, max_length=2)

    teamId: uuid.UUID | None = None


class SwimmingPoolUpdateReq(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    poolType: PoolType | None = None
    poolLength: PoolLength | None = None
    laneCount: int | None = Field(default=None, ge=1, le=20)

    streetAddress: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=64)
    postalCode: str | None = Field(default=None, min_length=2, max_length=16)
    countryIso: str | None = Field(default=None, min_length=2, max_length=2)

    teamId: uuid.UUID | None = None
    isActive: bool | None = None


class SwimmingPoolResp(BaseSchema):
    id: uuid.UUID
    name: str
    poolType: PoolType
    poolLength: PoolLength
    laneCount: int

    streetAddress: str
    city: str
    postalCode: str
    countryIso: str

    isActive: bool
    teamId: uuid.UUID | None = None

    createdAt: datetime
    updatedAt: datetime | None = None


class PaginatedSwimmingPoolResp(PaginatedResp[SwimmingPoolResp]):
    pass
