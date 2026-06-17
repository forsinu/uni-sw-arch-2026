from typing import Literal
from urllib.parse import quote

from pydantic import HttpUrl, PostgresDsn, computed_field, AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvHandler(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_file=".env",
    )

    # =========================
    # API / ROUTING
    # =========================

    AUTH_HOST: str = "auth-service"
    AUTH_PORT: int = 8000

    API_PREFIX: str
    API_VERSION: int = 1

    ROUTING_LOGGER_NAME: str = "federation-service.routing"
    ROUTING_LOG_REQUESTS: bool = True
    ROUTING_LOG_RESPONSES: bool = False

    # =========================
    # SECURITY / JWT
    # =========================

    JWT_ALGORITHM: str = "RS256"
    # JWT_KEY_SIZE: int = 4096
    JWT_KEY_ID: str
    JWT_PUBLIC_KEY_SERVICE_PATH: str = "/.well-known/jwks.json"
    SERVICE_TOKEN_PATH: str = "/run/secrets/service-token"

    # =========================
    # DATABASE
    # =========================

    DB_HOST: str = "federation-db"
    DB_NAME: str = "federation_db"

    DB_USER: str

    DB_PASSWD: str | None = None

    DB_PORT: int = 5432
    # DB_ECHO: bool = False

    DB_LOGGER_NAME: str = "federation-service.database"

    # =========================
    # LOGGING
    # =========================

    LOG_LEVEL: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    LOG_FORMAT: str = (
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    )

    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    APP_LOGGER_NAME: str = "federation-service"
    LOGGER_HANDLER_NAME: str = "auth-service.logger"

    # === RABBIMQ
    RABBITMQ_SERVICE_PORT: int = 5672
    RABBITMQ_SERVICE_USER: str
    RABBITMQ_SERVICE_PASSWORD: str
    RABBITMQ_SERVICE_VHOST: str = "/"
    RABBITMQ_SERVICE_HOST: str = "rabbitmq"

    @computed_field
    @property
    def DB_URL(self) -> str:
        url = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.DB_HOST,
            port=self.DB_PORT,
            username=self.DB_USER,
            password=self.DB_PASSWD,
            path=self.DB_NAME,
        )

        return str(url)

    @computed_field
    @property
    def AUTH_JWKS_URL(self) -> str:
        baseHost = self.AUTH_HOST.rstrip("/")
        cleanPath = self.JWT_PUBLIC_KEY_SERVICE_PATH.strip("/")
        url = HttpUrl.build(
            scheme="http",
            host=baseHost,
            port=self.AUTH_PORT,
            path=cleanPath,
        )

        return str(url)

    @computed_field
    @property
    def RABBITMQ_URL(self) -> str:
        encodedVhost = quote(self.RABBITMQ_SERVICE_VHOST, safe="")

        url = AnyUrl.build(
            scheme="amqp",
            username=self.RABBITMQ_SERVICE_USER,
            password=self.RABBITMQ_SERVICE_PASSWORD,
            host=self.RABBITMQ_SERVICE_HOST,
            port=self.RABBITMQ_SERVICE_PORT,
            path=encodedVhost,
        )

        return str(url)
