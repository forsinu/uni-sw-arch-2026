# src/schema/swim_event.py

from datetime import datetime
import uuid

from src.db.models.swim_event import RaceDistance, RaceGender, RaceStroke
from src.schemas.common import BaseSchema, PaginatedResp


class SwimEventCreateReq(BaseSchema):
    distance: RaceDistance
    stroke: RaceStroke
    gender: RaceGender
    startAt: datetime


class SwimEventUpdateReq(BaseSchema):
    distance: RaceDistance | None = None
    stroke: RaceStroke | None = None
    gender: RaceGender | None = None
    startAt: datetime | None = None


class SwimEventResp(BaseSchema):
    id: uuid.UUID
    meetingId: uuid.UUID
    distance: RaceDistance
    stroke: RaceStroke
    gender: RaceGender
    startAt: datetime


class PaginatedSwimEventResp(PaginatedResp[SwimEventResp]):
    pass
