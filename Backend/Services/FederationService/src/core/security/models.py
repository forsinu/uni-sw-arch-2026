# src/core/security/models.py

from datetime import datetime, timezone
import enum
from typing import Annotated
import uuid

from pydantic import BaseModel, BeforeValidator, field_serializer


class UserAccountRole(str, enum.Enum):
    DEFAULT = "DEFAULT"
    ADMIN = "ADMIN"


class AccessTokenPayload(BaseModel):
    sub: uuid.UUID
    role: UserAccountRole
    fed: str | None = None

    exp: Annotated[
        datetime,
        BeforeValidator(
            lambda dt: (
                datetime.fromtimestamp(dt, tz=timezone.utc)
                if isinstance(dt, (int, float))
                else dt
            )
        ),
    ]

    @field_serializer("exp", when_used="json")
    def serializeDatetimeToEpoch(self, dt: datetime) -> int:
        return int(dt.timestamp())
