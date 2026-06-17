import re
from typing import Literal

from pydantic import Field, field_validator

from src.schemas.common import BaseSchema


USERNAME_PATTERN = r"^[a-zA-Z0-9_](?:[a-zA-Z0-9_.]*[a-zA-Z0-9_])?$"
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterReq(BaseSchema):
    email: str | None = Field(
        default=None,
        min_length=3,
        max_length=320,
        examples=["user@example.com"],
    )

    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=USERNAME_PATTERN,
        examples=["mario.rossi"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["StrongPassword123!"],
    )


class LoginReq(BaseSchema):
    usernameOrEmail: str = Field(
        min_length=3,
        max_length=320,
        examples=["mario.rossi", "user@example.com"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["StrongPassword123!"],
    )

    @field_validator("usernameOrEmail")
    @classmethod
    def validateUsernameOrEmail(cls, value: str) -> str:
        value = value.strip()

        if "@" in value:
            if not re.fullmatch(EMAIL_PATTERN, value):
                raise ValueError("Invalid email format.")

        elif len(value) > 32:
            raise ValueError("Username must be at most 32 characters.")

        elif not re.fullmatch(USERNAME_PATTERN, value):
            raise ValueError("Invalid username format.")

        return value


class AccessTokenResp(BaseSchema):
    accessToken: str
    tt: Literal["bearer"] = "bearer"
