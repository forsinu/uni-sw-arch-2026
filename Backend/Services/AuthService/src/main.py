from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.api import api as apiV1

from src.api.dependencies import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.initModel()

    yield

    await db.closeConnection()


app = FastAPI(lifespan=lifespan)
app.include_router(apiV1, prefix="/api/v1")
