# src/db/session.py

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from logging import Logger, getLogger

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError

from src.db.errors import (
    DbConflictError,
    DbOperationError,
    DbUnavailableError,
)
from src.db.models.base import Base

# Important: this imports all model classes and registers them in Base.metadata
import src.db.models  # noqa: F401


class DatabaseHandler:
    def __init__(
        self,
        databaseUrl: str,
        echo: bool = False,
        logger: Logger | None = None,
        createTablesOnStartup: bool = True,
    ) -> None:
        self.databaseUrl = databaseUrl
        self.echo = echo
        self.logger = logger or getLogger(__name__)
        self.createTablesOnStartup = createTablesOnStartup

        self._engine: AsyncEngine | None = None
        self._sessionFactory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        self.logger.info("Initializing database engine")

        self._engine = create_async_engine(
            self.databaseUrl,
            echo=self.echo,
        )

        self._sessionFactory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        await self.healthCheck()

        if self.createTablesOnStartup:
            await self.createTables()

        self.logger.info("Database initialized successfully")

    async def createTables(self) -> None:
        self._ensureInitialized()

        assert self._engine is not None

        self.logger.info("Creating database tables if missing")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.logger.info("Database tables created successfully")

    async def dropTables(self) -> None:
        self._ensureInitialized()

        assert self._engine is not None

        self.logger.warning("Dropping database tables")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        self.logger.warning("Database tables dropped successfully")

    async def close(self) -> None:
        self.logger.info("Closing database engine")

        if self._engine is not None:
            await self._engine.dispose()

        self._engine = None
        self._sessionFactory = None

        self.logger.info("Database engine closed")

    def _ensureInitialized(self) -> None:
        if self._engine is None or self._sessionFactory is None:
            raise RuntimeError("DatabaseHandler has not been initialized")

    async def healthCheck(self) -> None:
        self._ensureInitialized()

        assert self._engine is not None

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        except Exception:
            self.logger.exception("Database health check failed")
            raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        self._ensureInitialized()

        assert self._sessionFactory is not None

        async with self._sessionFactory() as session:
            yield session

    @asynccontextmanager
    async def transaction(
        self,
        session: AsyncSession,
    ) -> AsyncIterator[AsyncSession]:
        try:
            async with session.begin():
                yield session

        except IntegrityError as exc:
            self.logger.warning("Database integrity error", exc_info=exc)
            raise DbConflictError("Database constraint violation") from exc

        except DBAPIError as exc:
            self.logger.error("Database driver error", exc_info=exc)

            if exc.connection_invalidated:
                raise DbUnavailableError("Database connection was invalidated") from exc

            raise DbOperationError("Database operation failed") from exc

        except SQLAlchemyError as exc:
            self.logger.error("SQLAlchemy error", exc_info=exc)
            raise DbOperationError("Database operation failed") from exc
