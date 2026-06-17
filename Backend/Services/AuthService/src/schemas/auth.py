# src/schema/auth.py

from typing import Literal

from pydantic import Field

from src.schemas.common import BaseSchema


class RegisterOrLoginReq(BaseSchema):
    email: str = Field(
        min_length=3,
        max_length=320,
        examples=["user@example.com"],
    )

    password: str = Field(
        min_length=8,
        max_length=128,
        examples=["StrongPassword123!"],
    )


class AccessTokenResp(BaseSchema):
    accessToken: str
    tt: Literal["bearer"] = "bearer"
