from fastapi import APIRouter
from fastapi import Depends

from src.api.v1.endpoints.auth import router as authRouter
from src.api.v1.endpoints.admin import router as adminRouter
from src.api.v1.endpoints.user import router as userRouter

from src.api.dependencies import accessAdminHandler, accessHandler


api = APIRouter()

api.include_router(
    authRouter,
    prefix="/auth",
    tags=["Authentication"],
)

api.include_router(
    adminRouter,
    prefix="/admin",
    tags=["Administrative"],
    dependencies=[Depends(accessAdminHandler)],
)

api.include_router(
    userRouter,
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(accessHandler)],
)
