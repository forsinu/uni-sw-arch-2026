from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import string
from typing import Annotated, Optional
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from cryptography.hazmat.primitives import serialization

import jwt
from jwt.utils import to_base64url_uint
from pydantic import BaseModel, BeforeValidator, field_serializer


from src.db.models.user_account import UserAccountRole
from src.core.env import EnvHandler


class RefreshTokenPayload(BaseModel):
    token: str
    exp: datetime


class AccessTokenPayload(BaseModel):
    sub: uuid.UUID
    role: UserAccountRole
    fed: Optional[str] = None
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

    # When the access token payload is transalted into a
    # json string convert the exp field into a timestamp
    @field_serializer("exp", when_used="json")
    def serialize_datetime_to_epoch(self, dt: datetime) -> int:
        return int(dt.timestamp())


class SecurityHandler:
    pass
