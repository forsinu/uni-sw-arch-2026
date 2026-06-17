# src/api/v1/api.py

from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as authRouter
from src.api.v1.endpoints.user import router as userRouter
from src.api.v1.endpoints.admin import router as adminRouter


api = APIRouter()

api.include_router(authRouter)
api.include_router(userRouter)
api.include_router(adminRouter)
