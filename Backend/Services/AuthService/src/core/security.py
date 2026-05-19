from datetime import datetime, timedelta, timezone
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

import jwt

import secrets

from src.core.environment import EnvironmentHandler


class SecurityHandler:
    def __init__(self, env: EnvironmentHandler):
        self.env = env
        self.ph = PasswordHasher()

    def hashPassword(self, password: str) -> str:
        return self.ph.hash(password)

    def verifyPassword(self, hash: str, plain: str) -> bool:
        try:
            return self.ph.verify(hash=hash, password=plain)

        except VerificationError:
            return False

    def generateRandomToken(self) -> dict:
        return {
            "token": secrets.token_urlsafe(nbytes=64),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.env.RT_EXP_MIN),
        }

    def generateAccessToken(self, userId: uuid.UUID, **kwargs) -> str:
        expiresAt = datetime.now(timezone.utc) + timedelta(minutes=self.env.AT_EXP_MIN)

        payload = {
            "sub": str(userId),
            "role": str(kwargs["role"]),
            "fed": kwargs.get("fed", "None"),
            "exp": expiresAt,
        }

        at = jwt.encode(
            payload=payload,
            key=self.env.SECRET_KEY,
            algorithm=self.env.JWT_ALGORITHM,
        )

        # TODO: Add Logging
        return at

    def verifyAccessToken(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self.env.SECRET_KEY,
                algorithms=[self.env.JWT_ALGORITHM],
            )

            return payload

        except jwt.ExpiredSignatureError:
            # TODO: Add Logging
            print("Token verification failed: Token has expired.")
            raise ValueError("Token has expired")

        except jwt.InvalidTokenError as e:
            print(f"Token verification failed: Invalid token ({e})")
            raise ValueError("Invalid token")
