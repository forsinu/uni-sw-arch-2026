from pathlib import Path
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

    AUTH_HOST: str = "federatuib-service"
    AUTH_PORT: int = 8000
    AUTH_PUB_KEY_PATH: str = ".well-known/jwks.json"
    JWT_ALGORITHM: str = "RS256"

    DB_HOST: str = "federation-db"
    DB_NAME: str = "federation_db"

    DB_USER: str
    # Local development fallback
    DB_PASSWD: str | None = None

    # Docker Swarm secret path
    DB_PASSWD_FILE: str | None = None

    def _read_secret_file(self, path: str) -> str:
        secret_path = Path(path)

        if not secret_path.exists():
            raise FileNotFoundError(f"Secret file not found: {path}")

        return secret_path.read_text(encoding="utf-8").strip()

    @computed_field
    @property
    def DB_PASSWORD(self) -> str:
        if self.DB_PASSWD_FILE:
            return self._read_secret_file(self.DB_PASSWD_FILE)

        if self.DB_PASSWD:
            return self.DB_PASSWD

        raise ValueError("Either DB_PASSWD_FILE or DB_PASSWD must be provided")

    @computed_field
    @property
    def DB_URL(self) -> str:
        url = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.DB_HOST,
            port=5432,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
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

        print(str(url))

        return str(url)
