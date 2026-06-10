from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from pydantic import PostgresDsn, computed_field, AnyHttpUrl


class EnvHandler(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_file=".env",
    )

    API_PREFIX: str

    DB_HOST: str = "competition-db"
    DB_NAME: str = "competition_db"

    DB_USER: str
    DB_PASSWD: str

    AUTH_HOST: str = "auth-service"
    AUTH_PORT: int = 8000
    AUTH_PUB_KEY_PATH: str = ".well-known/jwks.json"
    JWT_ALGORITHM: str = "RS256"

    @computed_field
    @property
    def DB_URL(self) -> str:
        url = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.DB_HOST,
            port=5432,
            username=self.DB_USER,
            password=self.DB_PASSWD,
            path=self.DB_NAME,
        )

        return str(url)

    @computed_field
    @property
    def AUTH_JWKS_URL(self) -> str:
        baseHost = self.AUTH_HOST.rstrip("/")
        cleanPath = self.AUTH_PUB_KEY_PATH.strip("/")
        url = AnyHttpUrl.build(
            scheme="http",
            host=baseHost,
            port=self.AUTH_PORT,
            path=cleanPath,
        )

        return str(url)
