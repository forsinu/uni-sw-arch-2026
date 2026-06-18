from datetime import datetime
import uuid

from pydantic import Field

from src.schemas.common import BaseSchema, PaginatedResp


class SwimMeetingRefereeAddReq(BaseSchema):
    meetingId: uuid.UUID

    refereeFederationId: str = Field(
        min_length=1,
        max_length=255,
    )


class SwimMeetingRefereeRemoveReq(BaseSchema):
    meetingId: uuid.UUID

    refereeFederationId: str = Field(
        min_length=1,
        max_length=255,
    )


class SwimMeetingRefereeRes(BaseSchema):
    id: uuid.UUID
    meetingId: uuid.UUID
    refereeFederationId: str
    assignedBy: uuid.UUID | None = None
    createdAt: datetime


class SwimMeetingRefereeInfoRes(BaseSchema):
    id: uuid.UUID
    meetingId: uuid.UUID
    refereeFederationId: str
    assignedBy: uuid.UUID | None = None
    createdAt: datetime

    # Optional fields if later you enrich the response by calling Federation Service.
    # firstName: str | None = None
    # lastName: str | None = None
    # federationRole: str | None = None


class PaginatedSwimMeetingRefereeResp(PaginatedResp[SwimMeetingRefereeRes]):
    pass
