from datetime import datetime
from typing import Annotated, Optional
import uuid
from pydantic import BaseModel, EmailStr, Field


class RegistrationReq(BaseModel):
    email: EmailStr
    password: Annotated[
        str,
        Field(min_length=12, max_length=64),
    ]


class LoginReq(BaseModel):
    email: EmailStr
    password: Annotated[
        str,
        Field(min_length=12, max_length=64),
    ]


class LogoutReq(BaseModel):
    userId: uuid.UUID


class TokenResp(BaseModel):
    at: str
    tt: str = "bearer"
