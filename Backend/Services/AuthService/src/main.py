from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status, Request
from fastapi.responses import RedirectResponse

from src.core.rabbitmq import RabbitMQHandler
from src.core.sec import SecurityHandler
from src.core.environment import EnvHandler
from src.core.log import LoggerHandler
from src.db.session import DatabaseHandler

from src.api.v1.api import api as apiV1


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

    return app


app = createApp()
