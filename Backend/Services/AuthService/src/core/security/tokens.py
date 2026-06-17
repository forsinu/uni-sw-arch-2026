from datetime import datetime, timedelta, timezone
from fastapi import Response

import logging
import secrets
import string
import uuid

import jwt

from src.core.environment import EnvHandler
from src.core.security.keys import RSAKeyProvider
from src.core.security.models import (
    AccessTokenPayload,
    RefreshTokenPayload,
)

from src.db.models.user_account import UserAccountRole


class TokenService:
    ALPHABET = string.ascii_letters + string.digits

    def __init__(
        self,
        env: EnvHandler,
        keyProvider: RSAKeyProvider,
        logger: logging.Logger,
    ) -> None:
        self.env = env
        self.keyProvider = keyProvider
        self.logger = logger

    def utcNow(self) -> datetime:
        return datetime.now(timezone.utc)

    def generateRandomPassword(self, length: int) -> str:
        return "".join(secrets.choice(self.ALPHABET) for _ in range(length))

    def generateRefreshToken(
        self,
        nowUtc: datetime | None = None,
    ) -> RefreshTokenPayload:
        nowUtc = nowUtc or self.utcNow()

        return RefreshTokenPayload(
            token=secrets.token_urlsafe(nbytes=64),
            exp=nowUtc + timedelta(minutes=self.env.RT_EXP_MIN),
        )

    def generateAccessToken(
        self,
        userId: uuid.UUID,
        role: UserAccountRole,
        fed: str | None = None,
        nowUtc: datetime | None = None,
    ) -> str:
        nowUtc = nowUtc or self.utcNow()
        expiresAt = nowUtc + timedelta(minutes=self.env.AT_EXP_MIN)

        payload = AccessTokenPayload(
            sub=userId,
            role=role,
            fed=fed,
            exp=expiresAt,
        )

        return jwt.encode(
            payload=payload.model_dump(mode="json"),
            key=self.keyProvider.getPrivateKey(),
            algorithm=self.env.JWT_ALGORITHM,
            headers={
                "kid": self.env.JWT_KEY_ID,
                "typ": "JWT",
            },
        )

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.keyProvider.getPublicKey(),
                algorithms=[self.env.JWT_ALGORITHM],
            )

            return AccessTokenPayload.model_validate(payload)

        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Token has expired") from exc

        except jwt.InvalidTokenError as exc:
            raise ValueError("Invalid token") from exc

    def setRefreshToken(
        self,
        response: Response,
        token: str,
    ) -> None:
        response.set_cookie(
            key=self.env.RT_COOKIE_NAME,
            value=token,
            max_age=self.env.RT_EXP_MIN * 60,
            httponly=True,
            secure=self.env.RT_COOKIE_SECURE,
            samesite=self.env.RT_COOKIE_SAMESITE,
        )

    def revokeRefreshToken(self, response: Response) -> None:
        response.delete_cookie(
            key=self.env.RT_COOKIE_NAME,
            httponly=True,
            secure=self.env.RT_COOKIE_SECURE,
            samesite=self.env.RT_COOKIE_SAMESITE,
        )
