from logging import Logger, getLogger
import uuid

from src.core.environment import EnvHandler
from src.core.security import (
    FederationIdentityHandler,
    AccessTokenPayload,
    FederationRole,
    AccessTokenVerifier,
    JWKSProvider,
    ServiceTokenHandler,
)


class SecurityHandler:
    def __init__(
        self,
        env: EnvHandler,
        logger: Logger | None = None,
    ) -> None:
        self.env = env
        self.logger = logger or getLogger(__name__)

        self.jwksProvider = JWKSProvider(
            env=env,
            logger=self.logger,
        )

        self.accessTokenVerifier = AccessTokenVerifier(
            env=env,
            jwksProvider=self.jwksProvider,
            logger=self.logger,
        )

        self.federationIdentityHandler = FederationIdentityHandler(
            logger=self.logger,
        )

        self.serviceTokenHandler = ServiceTokenHandler(self.env.SERVICE_TOKEN_PATH)

    async def initialize(self) -> None:
        await self.jwksProvider.initialize()

    async def refreshPublicKeys(self) -> None:
        await self.jwksProvider.refreshJWKS()

    def retrievePubKey(self) -> dict:
        return self.jwksProvider.getJWKS()

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        return self.accessTokenVerifier.verifyAccessToken(token)

    def extractFedFields(
        self,
        token: AccessTokenPayload,
    ) -> tuple[FederationRole, uuid.UUID]:
        return self.federationIdentityHandler.extractFedFields(token)

    def verifiyServiceToken(self, serviceToken: str):
        return self.serviceTokenHandler.verify(token=serviceToken)
