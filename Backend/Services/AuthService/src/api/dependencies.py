from typing import AsyncGenerator
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import SecurityHandler
from src.db.session import DatabaseHandler
from src.core.environment import EnvironmentHandler


env = EnvironmentHandler()

db = DatabaseHandler(env=env)
sec = SecurityHandler(env=env)

tokenHandler = HTTPBearer()


def envHandler() -> EnvironmentHandler:
    return env


def secHandler() -> SecurityHandler:
    return sec


async def dbHandler() -> AsyncGenerator[AsyncSession, None]:
    async for session in db.getDbSession():
        yield session
