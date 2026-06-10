import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.core.util import PaginationMetadata
from src.db.models.federation_members import FederationRole
from src.db.models.swimming_pool import PoolLength


class SwimmingTeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    shortName: str | None = Field(default=None, min_length=1, max_length=32)
    federationCode: str | None = Field(default=None, min_length=1, max_length=64)
    isActive: bool = True


class SwimmingTeamPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    shortName: str | None = Field(default=None, min_length=1, max_length=32)
    federationCode: str | None = Field(default=None, min_length=1, max_length=64)
    isActive: bool | None = None


class SwimmingTeamReq(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    shortName: str | None
    federationCode: str | None
    isActive: bool


class PaginatedSwimmingTeamReq(BaseModel):
    teams: list[SwimmingTeamReq]
    metadata: PaginationMetadata


class TeamAthleteCreate(BaseModel):
    birth: date
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    isActive: bool = True


class TeamMemberReq(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    federationId: str
    fedRole: FederationRole
    teamId: uuid.UUID | None
    birth: date | None
    memberCode: str
    firstName: str
    lastName: str
    isActive: bool


class PaginatedTeamMemberReq(BaseModel):
    members: list[TeamMemberReq]
    metadata: PaginationMetadata


class TeamPoolReq(BaseModel):
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


class PaginatedTeamPoolReq(BaseModel):
    pools: list[TeamPoolReq]
    metadata: PaginationMetadata
