from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from pydantic import PostgresDsn, computed_field


class EnvironmentHandler(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_file=".env",
    )

    JWT_ALGORITHM: str = "RS256"
    AT_EXP_MIN: int = 15
    RT_EXP_MIN: int = 5040
    PASSWORD_LEN: int = 12
    MAX_SESSIONS: int = 3

    PRIVATE_KEY_PATH: str = "keys/private_key.pem"
    PUBLIC_KEY_PATH: str = "keys/public_key.pem"

    MAX_ATTEMPTS: int = 5
    WINDOW_ATTEMPTS_MIN: int = 15

    DB_HOST: str = "auth-db"
    DB_NAME: str = "auth_db"

    DB_USER: str
    DB_PASSWD: str

    @computed_field
    @property
    def DB_URL(self) -> str:
        url = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            host=self.DB_HOST,
            port=5432,  # Maintain the defualt port for Postgres DB
            username=self.DB_USER,
            password=self.DB_PASSWD,
            path=self.DB_NAME,
        )

        return str(url)
