from datetime import date
import enum
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from src.core.util import PaginationMetadata


class FederationRole(str, enum.Enum):
    ATHLETE = "ATH"
    COACH = "COA"
    REFEREE = "REF"
    TEAM_MANAGER = "MGR"


class FederationMemberCreate(BaseModel):
    fedRole: FederationRole
    teamId: uuid.UUID | None = None

    birth: date | None = None

    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)

    isActive: bool = True

    @model_validator(mode="after")
    def validateRoleConstraints(self) -> "FederationMemberCreate":
        if self.fedRole == FederationRole.ATHLETE and self.birth is None:
            raise ValueError("birth is required for athletes")

        if self.fedRole != FederationRole.REFEREE and self.teamId is None:
            raise ValueError("teamId is required for non-referee members")

        return self


class FederationMemberPatch(BaseModel):
    fedRole: FederationRole | None = None
    teamId: uuid.UUID | None = None

    birth: date | None = None

    firstName: str | None = Field(default=None, min_length=1, max_length=100)
    lastName: str | None = Field(default=None, min_length=1, max_length=100)

    isActive: bool | None = None


class FederationMemberReq(BaseModel):
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


class PaginatedFederationMemberReq(BaseModel):
    members: list[FederationMemberReq]
    metadata: PaginationMetadata
