from datetime import datetime
import uuid

from pydantic import Field, model_validator

from src.db.models.swim_event_result import RaceResultStatus
from src.schemas.common import BaseSchema, PaginatedResp


class SwimEventResultUpsertReq(BaseSchema):
    federationId: str = Field(min_length=4, max_length=255)
    status: RaceResultStatus = RaceResultStatus.COMPLETED

    finalTimeMs: int | None = Field(default=None, gt=0)
    splitTimesMs: list[int] = Field(default_factory=list)
    disqualificationReason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validateResult(self):
        if any(splitTime <= 0 for splitTime in self.splitTimesMs):
            raise ValueError("All split times must be positive.")

        if self.status == RaceResultStatus.COMPLETED and self.finalTimeMs is None:
            raise ValueError("finalTimeMs is required for completed results.")

        if (
            self.status != RaceResultStatus.DSQ
            and self.disqualificationReason is not None
        ):
            raise ValueError("disqualificationReason is allowed only for DSQ results.")

        return self


class SwimEventResultResp(BaseSchema):
    id: uuid.UUID
    swimEventId: uuid.UUID
    federationId: str

    status: RaceResultStatus
    finalTimeMs: int | None = None
    splitTimesMs: list[int]
    disqualificationReason: str | None = None

    createdAt: datetime
    updatedAt: datetime | None = None


class PaginatedSwimEventResultResp(PaginatedResp[SwimEventResultResp]):
    pass
