from datetime import datetime, timezone
import enum
import re
from typing import Annotated, Optional
import uuid


import httpx
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
        self.jwksCache: Optional[dict] = None

    async def __loadPubKey(self):
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(self.env.AUTH_JWKS_URL)
                response.raise_for_status()

                self.jwksCache = response.json()

                if "keys" not in self.jwksCache:
                    raise RuntimeError(
                        "Invalid JWKS payload received: missing 'keys' dictionary element."
                    )

            except httpx.HTTPError as exc:
                raise RuntimeError(f"Failed to fetch JWKS from Auth Service: {exc}")

    async def initialize(self):
        await self.__loadPubKey()

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        if not self.jwksCache:
            raise RuntimeError(
                "SecurityHandler cannot verify incoming traffic: JWKS cache is empty."
            )

        try:
            header = jwt.get_unverified_header(token)
            tokenKID = header.get("kid")
            if not tokenKID:
                raise ValueError(
                    "Incoming token header is missing the required 'kid' parameter."
                )

            pubKey = None
            for keyData in self.jwksCache["keys"]:
                if keyData.get("kid") == tokenKID:
                    pubKey = jwt.PyJWK(keyData).key
                    break

            if not pubKey:
                raise ValueError(
                    "The signature key identifier ('kid') matched no keys in the cached JWKS."
                )

            payload = jwt.decode(
                jwt=token,
                key=pubKey,
                algorithms=[self.env.JWT_ALGORITHM],
            )
            return AccessTokenPayload.model_validate(payload)

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

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
