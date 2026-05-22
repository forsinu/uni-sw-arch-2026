from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Optional, Union
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from cryptography.hazmat.primitives import serialization

from fastapi import HTTPException, Response, status
import jwt
from jwt.utils import to_base64url_uint

import secrets

import string

from pydantic import BaseModel, field_serializer, BeforeValidator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from src.db.model import UserAccountRole
from src.core.environment import EnvironmentHandler
from src.core.util import handleDbOp


class SecurityHandler:
    def __init__(self, env: EnvironmentHandler):
        self.env = env
        self.alphabet = string.ascii_letters + string.digits
        self.ph = PasswordHasher()

        self.__loadKeys()

    class AccessTokenPayload(BaseModel):
        sub: uuid.UUID
        role: UserAccountRole
        fed: Optional[str] = None
        exp: Annotated[
            datetime,
            BeforeValidator(
                lambda dt: (
                    datetime.fromtimestamp(dt, tz=timezone.utc)
                    if isinstance(dt, int)
                    else dt
                )
            ),
        ]

        @field_serializer("exp", when_used="json")
        def serialize_datetime_to_epoch(self, dt: datetime) -> int:
            return int(dt.timestamp())

    class RefreshToken(BaseModel):
        token: str
        exp: datetime

    def __loadKeys(self):
        try:
            privKeyPath = Path(self.env.PRIVATE_KEY_PATH)
            pubKeyPath = Path(self.env.PUBLIC_KEY_PATH)

            if not privKeyPath.exists() or not pubKeyPath.exists():
                raise RuntimeError(
                    f"Cryptographic keys missing!"
                    f"Paths checked: {privKeyPath} and {pubKeyPath}"
                )

            with open(privKeyPath, "rb") as keyFile:
                self.privKeyPem = keyFile.read()

                self.privKey = serialization.load_pem_private_key(
                    self.privKeyPem, password=None
                )

            # 2. Load the raw Public Key string file contents
            with open(pubKeyPath, "rb") as keyFile:
                self.pubKeyPem = keyFile.read()

        except Exception as e:
            raise RuntimeError(
                f"Critical failure initializing RSA Cryptography: {str(e)}"
            )

    def hashPassword(self, password: str) -> str:
        return self.ph.hash(password)

    def verifyPassword(self, hash: str, plain: str) -> bool:
        try:
            return self.ph.verify(hash=hash, password=plain)

        except VerificationError:
            return False

    def generateRandomToken(self) -> RefreshToken:
        return SecurityHandler.RefreshToken(
            token=secrets.token_urlsafe(nbytes=64),
            exp=datetime.now(timezone.utc) + timedelta(minutes=self.env.RT_EXP_MIN),
        )

    def generateAccessToken(self, userId: uuid.UUID, **kwargs) -> str:
        expiresAt = datetime.now(timezone.utc) + timedelta(minutes=self.env.AT_EXP_MIN)

        payload = SecurityHandler.AccessTokenPayload(
            sub=userId,
            role=kwargs["role"],
            fed=kwargs.get("fed", "Noe"),
            exp=expiresAt,
        )

        at = jwt.encode(
            payload=payload.model_dump(mode="json"),
            key=self.privKeyPem,
            algorithm=self.env.JWT_ALGORITHM,
            headers={"kid": "auth-service-key-v1"},
        )

        # TODO: Add Logging
        return at

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.pubKeyPem,
                algorithms=[self.env.JWT_ALGORITHM],
            )

            return SecurityHandler.AccessTokenPayload.model_validate(payload)

        except jwt.ExpiredSignatureError:
            # TODO: Add Logging
            print("Token verification failed: Token has expired.")
            raise ValueError("Token has expired")

        except jwt.InvalidTokenError as e:
            print(f"Token verification failed: Invalid token ({e})")
            raise ValueError("Invalid token")

    def generateRandomPassword(self, length: int):
        return "".join([secrets.choice(self.alphabet)] for _ in range(length))

    def revokeRefreshToken(self, response: Response):
        response.set_cookie(
            key="rt",
            value="",
            max_age=0,
            httponly=True,
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

    async def checkRateLimit(
        self,
        db: AsyncSession,
        model: type,
        emailOrIdColumn: InstrumentedAttribute,
        targetValue: Union[str, uuid.UUID],
    ):

        timeThreshold = datetime.now(timezone.utc) - timedelta(
            minutes=self.env.WINDOW_ATTEMPTS_MIN
        )

        query = (
            select(model)
            .where(
                emailOrIdColumn == targetValue,
                model.attemptedAt >= timeThreshold,
            )
            .order_by(model.attemptedAt.desc())
            .limit(self.env.MAX_ATTEMPTS)
        )

        async with handleDbOp(db, "Internal Server Error"):
            result = await db.execute(query)

            attempts = result.scalars().all()

        if len(attempts) >= self.env.MAX_ATTEMPTS:
            allFailed = all(not att.wasSuccessfull for att in attempts)

            if allFailed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed actions. Locked out. Try again in {self.env.WINDOW_ATTEMPTS_MIN} minutes.",
                )
