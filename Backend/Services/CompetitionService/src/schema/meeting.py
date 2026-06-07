from datetime import date, datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict

from src.db.models.event_result import RaceResultStatus
from src.db.models.swim_event import RaceDistance, RaceGender, RaceStroke
from src.core.util import PaginationMetadata


class CreateOrAddSwimEventReq(BaseModel):
    id: uuid.UUID
    distance: RaceDistance
    stroke: RaceStroke
    gender: RaceGender
    startAt: datetime


class UpdateSwimEventReq(BaseModel):
    removeEvents: list[uuid.UUID] = []
    addEvents: list[CreateOrAddSwimEventReq] = []


# class AddSwimEventReq(BaseModel):
#     distance: RaceDistance
#     stroke: RaceStroke


class AthleteEntryReq(BaseModel):
    federationId: str
    enteredBy: str

    swimEventId: uuid.UUID


class AthleteResultReq(BaseModel):
    federationId: str
    splits: list[float] = []
    finalTime: Optional[float]

    status: RaceResultStatus

    swimEventId: uuid.UUID


class CreateMeetingReq(BaseModel):
    name: str
    poolLength: int

    entriesOpenAt: datetime
    entriesCloseAt: datetime

    startAt: date
    endAt: date

    # Team that organizes it
    organizedBy: Optional[uuid.UUID] = None
    # Team manager
    swimmingPoolId: Optional[uuid.UUID] = None

    swimEvents: Optional[list[CreateOrAddSwimEventReq]] = []


class UpdateMeetingInfoReq(BaseModel):
    name: Optional[str] = None
    poolLength: Optional[int] = None

    entriesOpenAt: Optional[datetime] = None
    entriesCloseAt: Optional[datetime] = None

    startAt: Optional[date] = None
    endAt: Optional[date] = None

    # Team that organizes it
    organizedBy: Optional[uuid.UUID] = None
    # Team manager
    createdBy: Optional[str] = None
    swimmingPoolId: Optional[uuid.UUID] = None

    # swimEvents: list[CreateSwimEventReq] = None


class MeetingListResp(BaseModel):
    id: uuid.UUID
    name: str
    startAt: date


class PaginatedMeetingsResp(BaseModel):
    metadata: PaginationMetadata
    results: list[MeetingListResp]


class MeetingInfoResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    poolLength: int

    entriesOpenAt: datetime
    entriesCloseAt: datetime

    startAt: date
    endAt: date

    # Team that organizes it
    organizedBy: Optional[uuid.UUID]
    # Team manager
    createdBy: Optional[str]
    swimmingPoolId: Optional[uuid.UUID]

    swimEvents: list[CreateOrAddSwimEventReq]
