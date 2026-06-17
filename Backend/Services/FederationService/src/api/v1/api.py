from fastapi import APIRouter

from src.api.v1.endpoints.federation_members import router as federationMembersRouter
from src.api.v1.endpoints.swimming_pools import router as swimmingPoolsRouter
from src.api.v1.endpoints.swimming_teams import router as swimmingTeamsRouter


api = APIRouter()

api.include_router(swimmingTeamsRouter)
api.include_router(swimmingPoolsRouter)
api.include_router(federationMembersRouter)
