from datetime import datetime, timezone
import enum
import re
from typing import Annotated, Optional
import uuid


import jwt
from pydantic import BaseModel, BeforeValidator, field_serializer

from src.core.env import EnvHandler


class UserAccountRole(str, enum.Enum):
    DEFAULT = "DEFAULT"
    ADMIN = "ADMIN"


class FederationRole(str, enum.Enum):
    ATHLETE = "ATH"
    COACH = "COA"
    REFEREE = "REF"
    TEAM_MANAGER = "MGR"


# class RefreshTokenPayload(BaseModel):
#     token: str
#     exp: datetime


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
    FED_ID_PATTERN = re.compile(
        r"^(.+?)-([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})-(.*)$"
    )

    def __init__(self, env: EnvHandler):
        self.env = env

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.pubKeyPem,
                algorithms=[self.env.JWT_ALGORITHM],
            )
            return AccessTokenPayload.model_validate(payload)

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")

        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def extractFedFields(
        self, token: AccessTokenPayload
    ) -> tuple[FederationRole, uuid.UUID]:
        fedId = token.fed
        if not fedId:
            raise ValueError("Provided Federation Id is missing!")

        match = self.FED_ID_PATTERN.match(fedId)
        if not match:
            raise ValueError("Provided Federation Id structure is incorrect!")

        rolePrefix = match.group(1)
        teamIdStr = match.group(2)

        try:
            role = FederationRole(rolePrefix)
        except ValueError:
            raise ValueError(
                f"Invalid Federation ID structure! '{rolePrefix}' "
                f"is not a recognized federation role."
            )

        # 2. Safely parse into a UUID object
        try:
            teamId = uuid.UUID(teamIdStr)
        except ValueError:
            raise ValueError(
                f"Invalid Federation ID structure! '{teamIdStr}' "
                f"is not a valid UUID string."
            )

        return role, teamId

    def retrievePubKey(self):
        pass
