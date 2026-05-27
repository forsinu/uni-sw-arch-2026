from fastapi import APIRouter, Depends

from src.api.dependencies import accessAdminHandler, accessHandler
from src.api.v1.endpoints.auth import router as authRouter
from src.api.v1.endpoints.user import router as userRouter
from src.api.v1.endpoints.admin import router as adminRouter

api = APIRouter()

api.include_router(
    authRouter,
    prefix="/auth",
    tags=["Authentication"],
)

api.include_router(
    userRouter,
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(accessHandler)],
)

api.include_router(
    adminRouter,
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(accessAdminHandler)],
)
