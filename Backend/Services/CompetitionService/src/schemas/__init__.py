from src.schemas.common import MessageResp, PaginatedResp, PaginationMetadata

from src.schemas.swim_meeting import (
    PaginatedSwimMeetingResp,
    SwimMeetingCreateReq,
    SwimMeetingResp,
    SwimMeetingStatusUpdateReq,
    SwimMeetingUpdateReq,
)

from src.schemas.swim_event import (
    PaginatedSwimEventResp,
    SwimEventCreateReq,
    SwimEventResp,
    SwimEventUpdateReq,
)

from src.schemas.swim_event_entry import (
    PaginatedSwimEventEntryResp,
    SwimEventEntryCreateReq,
    SwimEventEntryResp,
    SwimEventEntryUpdateReq,
)

from src.schemas.swim_event_result import (
    PaginatedSwimEventResultResp,
    SwimEventResultResp,
    SwimEventResultUpsertReq,
)

__all__ = [
    "MessageResp",
    "PaginatedResp",
    "PaginationMetadata",
    "PaginatedSwimMeetingResp",
    "SwimMeetingCreateReq",
    "SwimMeetingResp",
    "SwimMeetingStatusUpdateReq",
    "SwimMeetingUpdateReq",
    "PaginatedSwimEventResp",
    "SwimEventCreateReq",
    "SwimEventResp",
    "SwimEventUpdateReq",
    "PaginatedSwimEventEntryResp",
    "SwimEventEntryCreateReq",
    "SwimEventEntryResp",
    "SwimEventEntryUpdateReq",
    "PaginatedSwimEventResultResp",
    "SwimEventResultResp",
    "SwimEventResultUpsertReq",
]
