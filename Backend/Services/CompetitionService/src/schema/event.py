from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from src.db.models.event_result import RaceResultStatus
from src.core.util import PaginationMetadata


# class PaginatedMeetingsResp(BaseModel):
#     metadata: PaginationMetadata
#     results: list[MeetingListResp]


class SubscribeEventReq(BaseModel):
    eventId: uuid.UUID
    entryTime: float


class SubscribeAthleteReq(BaseModel):
    athleteFedId: str
    meetingId: uuid.UUID

    events: list[SubscribeEventReq]


class MeetingEntriesResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    federationId: str
    eventId: uuid.UUID
    entryTime: float
    enteredBy: str


class PaginatedMeetingEntriesResp(BaseModel):
    metadata: PaginationMetadata
    entries: list[MeetingEntriesResp]


class MeetingResultsResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    federationId: str
    splits: list[float] = Field(default_factory=list)
    finalTime: Optional[float] = None

    status: RaceResultStatus


class PaginatedMeetingResultsResp(BaseModel):
    metadata: PaginationMetadata
    results: list[MeetingResultsResp]


class UpdateMeetingEntryReq(BaseModel):
    entryTime: float


class InsertResultsReq(BaseModel):
    federationId: str
    splits: list[float]
    finalTime: Optional[float] = None
    status: RaceResultStatus
    swimEventId: uuid.UUID
