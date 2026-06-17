from datetime import datetime, timezone
from typing import Annotated

import enum
import uuid

from pydantic import BaseModel, BeforeValidator, field_serializer
from src.db.models.user_account import UserAccountRole


class RefreshTokenPayload(BaseModel):
    token: str
    exp: datetime


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
