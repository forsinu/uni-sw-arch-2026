from fastapi import APIRouter

from src.api.v1.endpoints.member import router as memberRouter
from src.api.v1.endpoints.team import router as teamRouter
from src.api.v1.endpoints.pool import router as poolRouter

api = APIRouter()

# api.include_router(

# )
api.include_router(
    memberRouter,
    prefix="/members",
    tags=["Federation Members"],
)

api.include_router(
    teamRouter,
    prefix="/team",
    tags=["Federation Swimming Teams"],
)

api.include_router(
    poolRouter,
    prefix="/pool",
    tags=["Federation Swimming Pools"],
)
