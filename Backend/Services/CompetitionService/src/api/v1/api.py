# src/api/v1/api.py

from fastapi import APIRouter

from src.api.v1.endpoints.swim_event_entry import router as swimEventEntriesRouter
from src.api.v1.endpoints.swim_event_result import router as swimEventResultsRouter
from src.api.v1.endpoints.swim_event import router as swimEventsRouter
from src.api.v1.endpoints.swim_meetings import router as swimMeetingsRouter
from src.api.v1.endpoints.swim_meeting_referees import (
    router as swimMeetingRefereeRouter,
)


api = APIRouter()

api.include_router(swimMeetingsRouter)
api.include_router(swimEventsRouter)
api.include_router(swimEventEntriesRouter)
api.include_router(swimEventResultsRouter)
api.include_router(swimMeetingRefereeRouter)
