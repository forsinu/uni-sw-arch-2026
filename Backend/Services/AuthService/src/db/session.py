from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from typing import AsyncGenerator

from src.core.environment import EnvironmentHandler
from src.db.model import Base


class DatabaseHandler:
    def __init__(self, env: EnvironmentHandler):
        self.engine = create_async_engine(
            env.DB_URL,
            pool_pre_ping=True,
            echo=False,
        )

        self.session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def initModel(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def closeConnection(self):
        await self.engine.dispose()

    async def getDbSession(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session() as s:
            try:
                yield s

            except Exception as e:
                # TODO: Add Logging
                print(f"[!] DB Error: {e}")
                await s.rollback()

            finally:
                await s.close()
