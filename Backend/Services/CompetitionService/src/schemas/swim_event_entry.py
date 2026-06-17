from datetime import datetime
import uuid

from pydantic import Field

from src.schemas.common import BaseSchema, PaginatedResp


class SwimEventEntryCreateReq(BaseSchema):
    federationId: str = Field(min_length=4, max_length=255)
    entryTimeMs: int = Field(gt=0)


class SwimEventEntryUpdateReq(BaseSchema):
    entryTimeMs: int = Field(gt=0)


class SwimEventEntryResp(BaseSchema):
    id: uuid.UUID
    swimEventId: uuid.UUID
    federationId: str
    entryTimeMs: int
    enteredBy: str
    createdAt: datetime
    updatedAt: datetime | None = None


class PaginatedSwimEventEntryResp(PaginatedResp[SwimEventEntryResp]):
    pass
