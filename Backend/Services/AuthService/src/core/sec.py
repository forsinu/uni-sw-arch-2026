from datetime import datetime
import logging
import uuid

from fastapi import Response

from src.core.environment import EnvHandler
from src.core.security.keys import RSAKeyProvider
from src.core.security.models import (
    AccessTokenPayload,
    RefreshTokenPayload,
)
from src.core.security.password import PasswordService
from src.core.security.tokens import TokenService
from src.db.models.user_account import UserAccountRole


class SecurityHandler:
    def __init__(
        self,
        env: EnvHandler,
        logger: logging.Logger,
    ) -> None:
        self.env = env
        self.logger = logger

        self.keyProvider = RSAKeyProvider(
            env=env,
            logger=logger,
        )

        self.passwordService = PasswordService(
            logger=logger,
        )

        self.tokenService = TokenService(
            env=env,
            keyProvider=self.keyProvider,
            logger=logger,
        )

    async def initialize(self) -> None:
        await self.keyProvider.initialize()

    def generateRandomPassword(self, length: int) -> str:
        return self.tokenService.generateRandomPassword(length)

    def hashPassword(self, password: str) -> str:
        return self.passwordService.hashPassword(password)

    def verifyPassword(self, hashedPassword: str, plainPassword: str) -> bool:
        return self.passwordService.verifyPassword(
            hashedPassword=hashedPassword,
            plainPassword=plainPassword,
        )

    def generateRefreshToken(self, nowUtc: datetime) -> RefreshTokenPayload:
        return self.tokenService.generateRefreshToken(nowUtc=nowUtc)

    def generateAccessToken(
        self,
        userId: uuid.UUID,
        role: UserAccountRole,
        nowUtc: datetime,
        fed: str | None = None,
    ) -> str:
        return self.tokenService.generateAccessToken(
            userId=userId,
            role=role,
            fed=fed,
            nowUtc=nowUtc,
        )

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        return self.tokenService.verifyAccessToken(token)

    def setRefreshToken(
        self,
        response: Response,
        token: str,
    ) -> None:
        self.tokenService.setRefreshToken(
            response=response,
            token=token,
        )

    def revokeRefreshToken(self, response: Response) -> None:
        self.tokenService.revokeRefreshToken(response)

    def generateJWKS(self) -> dict:
        return self.keyProvider.getJWKS()
