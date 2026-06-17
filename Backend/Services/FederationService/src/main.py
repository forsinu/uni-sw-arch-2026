from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.core.sec import SecurityHandler
from src.core.environment import EnvHandler
from src.core.log import LoggerHandler
from src.db.session import DatabaseHandler
from src.core.rabbitmq import RabbitMQHandler

from src.api.v1.api import api as apiV1


API_VERSIONS = {
    1: {
        "router": [apiV1],
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

    for router in selectedAPI["router"]:
        app.include_router(
            router=router,
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
            logger=loggerHandler.database,
        )

        security = SecurityHandler(env, logger)

        rabbitmq = RabbitMQHandler(env, logger=logger)

        await security.initialize()
        await database.initialize()
        await rabbitmq.initialize()

        app.state.envHandler = env
        app.state.loggerHandler = loggerHandler
        app.state.dbHandler = database
        app.state.secHandler = security
        app.state.rabbitmqHandler = rabbitmq

        includeAPIRouter(app)

        yield

        #  await rabbitMq.close()
        logger.info("Shutting down DB")
        await database.close()
        await rabbitmq.close()
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

    return app


app = createApp()
