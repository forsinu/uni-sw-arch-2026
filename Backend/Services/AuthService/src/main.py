from contextlib import asynccontextmanager

#  from datetime import datetime, timezone
from fastapi import Depends, FastAPI, status

from typing import Annotated


from src.core.env import EnvHandler
from src.core.security import SecurityHandler
from src.db.session import DatabaseHandler
from src.api.v1.api import api as apiV1

from src.api.dependencies import secHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    env = EnvHandler()

    database = DatabaseHandler(env=env)
    security = SecurityHandler(env=env)

    await database.initModel()

    app.state.env = env
    app.state.database = database
    app.state.security = security

    yield

    await database.closeConnection()


app = FastAPI(lifespan=lifespan)

app.include_router(apiV1, prefix="/api/v1")


@app.get("/.well-known/jwks.json", status_code=status.HTTP_200_OK)
async def getJWKS(
    # request: Request,
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):
    return sec.generateJWKS()
