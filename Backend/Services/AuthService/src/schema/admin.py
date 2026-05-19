from typing import Annotated
import uuid
from pydantic import BaseModel, EmailStr, Field


class UserAssociationReq(BaseModel):
    federationId: Annotated[str, Field(max_length=32)]
    userId: uuid.UUID

    email: EmailStr
    password: Annotated[str, Field(min_length=12, max_length=64)]
