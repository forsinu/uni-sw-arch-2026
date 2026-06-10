import uuid

from pydantic import BaseModel, ConfigDict, Field

from src.core.util import PaginationMetadata
from src.db.models.swimming_pool import PoolLength, PoolType


class SwimmingPoolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    lenPool: PoolLength
    numbOfLane: int = Field(ge=1, le=20)
    streetAddr: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=32)
    postalCode: str = Field(min_length=1, max_length=16)
    countryIso: str = Field(min_length=2, max_length=2)
    teamId: uuid.UUID | None = None


class SwimmingPoolPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    lenPool: PoolLength | None = None
    numbOfLane: int | None = Field(default=None, ge=1, le=20)
    streetAddr: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=32)
    postalCode: str | None = Field(default=None, min_length=1, max_length=16)
    countryIso: str | None = Field(default=None, min_length=2, max_length=2)
    teamId: uuid.UUID | None = None


class SwimmingPoolReq(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    lenPool: PoolLength
    numbOfLane: int
    streetAddr: str
    city: str
    postalCode: str
    countryIso: str
    teamId: uuid.UUID | None


class PaginatedSwimmingPoolReq(BaseModel):
    pools: list[SwimmingPoolReq]
    metadata: PaginationMetadata
