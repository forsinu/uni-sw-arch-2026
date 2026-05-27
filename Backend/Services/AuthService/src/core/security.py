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
    ALPHABET = string.ascii_letters + string.digits

    def __init__(self, env: EnvHandler):
        self.env = env
        self.ph = PasswordHasher()

        self.__loadKeys()

    def __loadKeys(self):
        try:
            privKeyPath = Path(self.env.PRIVATE_KEY_PATH)
            pubKeyPath = Path(self.env.PUBLIC_KEY_PATH)

            if not privKeyPath.exists() or not pubKeyPath.exists():
                raise RuntimeError(
                    f"Cryptographic keys missing! Paths checked: {privKeyPath} and {pubKeyPath}"
                )

            with open(privKeyPath, "rb") as keyFile:
                self.privKeyPem = keyFile.read()
                self.privKey = serialization.load_pem_private_key(
                    self.privKeyPem, password=None
                )

            with open(pubKeyPath, "rb") as keyFile:
                self.pubKeyPem = keyFile.read()

        except Exception as e:
            raise RuntimeError(
                f"Critical failure initializing RSA Cryptography: {str(e)}"
            )

    def generateRandomPassword(self, length: int) -> str:
        return "".join(secrets.choice(SecurityHandler.ALPHABET) for _ in range(length))

    def hashPassword(self, password: str) -> str:
        return self.ph.hash(password)

    def verifyPassword(self, hash: str, plain: str) -> bool:
        try:
            return self.ph.verify(hash=hash, password=plain)
        except VerificationError:
            return False

    def generateRandomToken(self, nowUtc: datetime) -> RefreshTokenPayload:
        return RefreshTokenPayload(
            token=secrets.token_urlsafe(nbytes=64),
            exp=(nowUtc + timedelta(minutes=self.env.RT_EXP_MIN)),
        )

    def generateAccessToken(
        self,
        userId: uuid.UUID,
        role: UserAccountRole,
        nowUtc: datetime,
        fed: Optional[str] = None,
    ) -> str:
        expiresAt = nowUtc + timedelta(minutes=self.env.AT_EXP_MIN)

        payload = AccessTokenPayload(
            sub=userId,
            role=role,
            fed=fed,
            exp=expiresAt,
        )

        at = jwt.encode(
            payload=payload.model_dump(mode="json"),
            key=self.privKeyPem,
            algorithm=self.env.JWT_ALGORITHM,
            headers={"kid": "auth-service-key-v1"},
        )

        return at

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

    def setRefreshToken(self, response, token: str):
        response.set_cookie(
            key="rt",
            value=token,
            max_age=self.env.RT_EXP_MIN * 60,
            httponly=True,
            # secure=True,
            samesite="lax",
        )

    def revokeRefreshToken(self, response):
        response.set_cookie(
            key="rt",
            value="",
            max_age=0,
            httponly=True,
            secure=True,  # Production-ready best practice
            samesite="lax",
        )

    def generateJWKS(self):
        pubNumbs = self.privKey.public_key().public_numbers()
        jwk = {
            "kty": "RSA",
            "key_ops": ["verify"],
            "alg": "RS256",
            "kid": "auth-service-key-v1",
            "n": to_base64url_uint(pubNumbs.n).decode("ascii"),
            "e": to_base64url_uint(pubNumbs.e).decode("ascii"),
        }
        return {"keys": [jwk]}
