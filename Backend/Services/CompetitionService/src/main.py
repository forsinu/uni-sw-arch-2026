from contextlib import asynccontextmanager
from pathlib import Path

#  from datetime import datetime, timezone
from fastapi import FastAPI


from src.core.env import EnvHandler
from src.core.security import SecurityHandler
from src.db.session import DatabaseHandler
# from src.api.v1.api import api as apiV1

from src.api.v1.api import api as apiV1

API_VERSION = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    env = EnvHandler()

    database = DatabaseHandler(env=env)
    security = SecurityHandler(env=env)

    await database.initModel()

    await security.initialize()

    app.state.env = env
    app.state.database = database
    app.state.security = security

    app.openapi_url = str(Path(env.API_PREFIX) / "openapi.json")

    yield

    await database.closeConnection()


app = FastAPI(lifespan=lifespan)

app.include_router(apiV1, prefix=API_VERSION)
