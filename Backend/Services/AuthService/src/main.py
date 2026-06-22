from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import secrets

from fastapi import FastAPI, status, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.core.rabbitmq import RabbitMQHandler
from src.core.sec import SecurityHandler
from src.core.environment import EnvHandler
from src.core.log import LoggerHandler
from src.db.session import DatabaseHandler
from src.db.repositories import (
    RefreshTokenRepository,
    UserAccountHistoryRepository,
    UserAccountRepository,
)
from src.db.models.user_account import UserAccountRole, UserAccountStatus

from src.api.v1.api import api as apiV1


@dataclass(frozen=True)
class StartupAdminCredentials:
    username: str
    password: str


API_VERSIONS = {
    1: {
        "router": apiV1,
        "prefix": "/api/v1",
    },
}


def includeAPIRouter(app: FastAPI) -> None:
    env = app.state.envHandler
    selectedAPI = API_VERSIONS.get(env.API_VERSION)

    if selectedAPI is None:
        supportedVersions = ", ".join(str(version) for version in API_VERSIONS)

        raise RuntimeError(
            f"Unsupported API version: {env.API_VERSION}. "
            f"Supported versions: {supportedVersions}"
        )

    app.include_router(
        selectedAPI["router"],
        prefix=selectedAPI["prefix"],
    )


async def resolveStartupAdminUsername(
    userRepository: UserAccountRepository,
    preferredUsername: str,
) -> str:
    existingUser = await userRepository.getUserByUsername(preferredUsername)

    if existingUser is None:
        return preferredUsername

    return f"admin_{secrets.token_hex(4)}"


async def createStartupAdminIfMissing(
    env: EnvHandler,
    database: DatabaseHandler,
    security: SecurityHandler,
):
    if not env.CREATE_ADMIN_ON_STARTUP:
        return None

    async with database.session() as session:
        async with database.transaction(session):
            userRepository = UserAccountRepository(session)
            historyRepository = UserAccountHistoryRepository(session)

            existingAdmin = await userRepository.getAdminUser()

            if existingAdmin is not None:
                return None

            nowUtc = datetime.now(timezone.utc)
            username = await resolveStartupAdminUsername(
                userRepository=userRepository,
                preferredUsername=env.STARTUP_ADMIN_USERNAME,
            )
            # password = security.generateRandomPassword(
            #     max(env.PASSWORD_MIN_LEN, env.STARTUP_ADMIN_PASSWORD_LEN),
            # )

            user = await userRepository.createUser(
                username=username,
                email=env.STARTUP_ADMIN_EMAIL,
                hashedPassword=security.hashPassword(env.STARTUP_ADMIN_PASSWORD),
                userRole=UserAccountRole.ADMIN,
                accountStatus=UserAccountStatus.ACTIVE,
                createdAt=nowUtc,
            )

            await historyRepository.createHistoryEntry(
                userAccountId=user.id,
                statusChangedTo=UserAccountStatus.ACTIVE,
                changedBy=user.id,
                reason="Initial startup administrator account provisioned.",
                changedAt=nowUtc,
            )

            # return StartupAdminCredentials(
            #     username=username,
            #     password=password,
            # )


async def revokeRefreshTokensOnStartup(database: DatabaseHandler) -> int:
    async with database.session() as session:
        async with database.transaction(session):
            repository = RefreshTokenRepository(session)

            return await repository.revokeAllActiveRefreshTokens(
                rotatedAt=datetime.now(timezone.utc),
            )


def createApp() -> FastAPI:
    env = EnvHandler()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        loggerHandler = LoggerHandler(env)
        loggerHandler.initialize()

        logger = loggerHandler.app

        logger.info("Starting DB")

        database = DatabaseHandler(
            databaseUrl=env.DB_URL,
            echo=env.DB_ECHO,
            logger=loggerHandler.database,
        )

        security = SecurityHandler(env, logger)

        await database.initialize()
        await createStartupAdminIfMissing(
            env=env,
            database=database,
            security=security,
        )

        # if startupAdminCredentials is not None:
        #     logger.warning(
        #         "Startup admin credentials: username=%s password=%s",
        #         startupAdminCredentials.username,
        #         startupAdminCredentials.password,
        #     )
        # else:
        #     logger.info("Startup admin account already present or disabled")

        revokedRefreshTokens = await revokeRefreshTokensOnStartup(database)
        logger.info(
            "Invalidated %s active refresh token(s) on startup",
            revokedRefreshTokens,
        )

        await security.initialize()

        rabbitmq = RabbitMQHandler(
            env=env,
            sec=security,
            sessionFactory=database._sessionFactory,
            logger=logger,
        )

        await rabbitmq.initialize()

        app.state.envHandler = env
        app.state.loggerHandler = loggerHandler
        app.state.dbHandler = database
        app.state.secHandler = security
        app.state.rabbitmqHandler = rabbitmq

        includeAPIRouter(app)

        yield

        logger.info("Shutting down DB")
        await database.close()
        logger.info("Application stopped")

    app = FastAPI(
        lifespan=lifespan,
        root_path=env.API_PREFIX,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="docs")

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    @app.get("/.well-known/jwks.json", status_code=status.HTTP_200_OK)
    async def getJWKS(request: Request):
        return request.app.state.secHandler.generateJWKS()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = createApp()
