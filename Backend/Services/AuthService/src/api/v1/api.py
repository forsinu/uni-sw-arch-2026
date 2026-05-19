from fastapi import APIRouter
from src.api.v1.endpoints.auth import router as authRouter


api = APIRouter()

api.include_router(authRouter, prefix="/auth", tags=["Authentication"])
