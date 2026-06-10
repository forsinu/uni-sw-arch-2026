from fastapi import APIRouter

from src.api.v1.endpoints.event import router as eventRouter
from src.api.v1.endpoints.meeting import router as meetingRouter

api = APIRouter()

api.include_router(
    eventRouter,
    prefix="/event",
    tags=["Event Manager"],
)

api.include_router(
    meetingRouter,
    prefix="/meeting",
    tags=["Meets Manager"],
)
