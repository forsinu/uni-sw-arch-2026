import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import string
from typing import Annotated, Optional
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

import jwt
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

        self.privKeyPem = None
        self.pubKeyPem = None
        self._cachedJWK = None

        self.__loadSwarmKeys()

    def __loadSwarmKeys(self):
        privPath = Path(self.env.PRIVATE_KEY_PATH)
        pubPath = Path(self.env.PUBLIC_KEY_PATH)

        if not privPath.exists() or not pubPath.exists():
            raise RuntimeError("Missing required Swarm Secrets for JWT keys.")

        with privPath.open() as f:
            self.privKeyPem = f.read().encode("utf-8")

        with pubPath.open() as f:
            self.pubKeyPem = f.read().encode("utf-8")

        try:
            keyObj = serialization.load_pem_public_key(
                self.pubKeyPem, backend=default_backend()
            )
            public_numbers = keyObj.public_numbers()

            def int_to_base64url(num: int) -> str:
                num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder="big")
                return base64.urlsafe_b64encode(num_bytes).rstrip(b"=").decode("utf-8")

            self._cachedJWK = {
                "kty": "RSA",
                "use": "sig",
                "key_ops": ["verify"],
                "alg": self.env.JWT_ALGORITHM,
                "kid": "auth-service-key-v1",
                "n": int_to_base64url(public_numbers.n),
                "e": int_to_base64url(public_numbers.e),
            }
        except Exception as e:
            raise RuntimeError(f"Failed to generate JWK from public key: {str(e)}")

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
        return {"keys": [self._cachedJWK]}
