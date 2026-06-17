# src/schema/swim_meeting.py

from datetime import date, datetime
import uuid

from pydantic import Field, model_validator

from src.db.models.swim_meeting import MeetingPoolLength, SwimMeetingStatus
from src.schemas.common import BaseSchema, PaginatedResp


class SwimMeetingCreateReq(BaseSchema):
    name: str = Field(min_length=2, max_length=255)
    poolLength: MeetingPoolLength

    entriesOpenAt: datetime
    entriesCloseAt: datetime

    startDate: date
    endDate: date

    organizerTeamId: uuid.UUID | None = None
    swimmingPoolId: uuid.UUID | None = None

    status: SwimMeetingStatus = SwimMeetingStatus.UPCOMING

    @model_validator(mode="after")
    def validateMeetingDates(self):
        if self.entriesOpenAt >= self.entriesCloseAt:
            raise ValueError("entriesOpenAt must be before entriesCloseAt.")

        if self.startDate > self.endDate:
            raise ValueError("startDate must be before or equal to endDate.")

        return self


class SwimMeetingUpdateReq(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    poolLength: MeetingPoolLength | None = None

    entriesOpenAt: datetime | None = None
    entriesCloseAt: datetime | None = None

    startDate: date | None = None
    endDate: date | None = None

    organizerTeamId: uuid.UUID | None = None
    swimmingPoolId: uuid.UUID | None = None

    status: SwimMeetingStatus | None = None


class SwimMeetingStatusUpdateReq(BaseSchema):
    status: SwimMeetingStatus


class SwimMeetingResp(BaseSchema):
    id: uuid.UUID
    name: str
    poolLength: MeetingPoolLength
    status: SwimMeetingStatus

    entriesOpenAt: datetime
    entriesCloseAt: datetime

    startDate: date
    endDate: date

    organizerTeamId: uuid.UUID | None = None
    swimmingPoolId: uuid.UUID | None = None

    createdAt: datetime
    updatedAt: datetime | None = None


class PaginatedSwimMeetingResp(PaginatedResp[SwimMeetingResp]):
    pass
