# src/core/security/jwks.py

from logging import Logger, getLogger

import httpx
import jwt

from src.core.environment import EnvHandler
from src.core.security import AccessTokenPayload


class JWKSProvider:
    def __init__(
        self,
        env: EnvHandler,
        logger: Logger | None = None,
    ) -> None:
        self.env = env
        self.logger = logger or getLogger(__name__)

        self._jwksCache: dict | None = None

    async def initialize(self) -> None:
        await self.refreshJWKS()

    async def refreshJWKS(self) -> None:
        self.logger.info("Fetching JWKS from Auth Service")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.env.AUTH_JWKS_URL)
                response.raise_for_status()

        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Failed to fetch JWKS from Auth Service: {self.env.AUTH_JWKS_URL}"
            ) from exc

        jwksPayload = response.json()

        if "keys" not in jwksPayload:
            raise RuntimeError("Invalid JWKS payload received: missing 'keys' field.")

        if not isinstance(jwksPayload["keys"], list):
            raise RuntimeError("Invalid JWKS payload received: 'keys' must be a list.")

        self._jwksCache = jwksPayload

        self.logger.info("JWKS cache loaded successfully")

    def _ensureInitialized(self) -> None:
        if self._jwksCache is None:
            raise RuntimeError(
                "JWKSProvider has not been initialized. Call initialize() first."
            )

    def getJWKS(self) -> dict:
        self._ensureInitialized()
        assert self._jwksCache is not None

        return self._jwksCache

    def getPublicKeyByKid(self, kid: str):
        self._ensureInitialized()
        assert self._jwksCache is not None

        for keyData in self._jwksCache["keys"]:
            if keyData.get("kid") == kid:
                return jwt.PyJWK(keyData).key

        raise ValueError(
            "The signature key identifier ('kid') matched no keys in cached JWKS."
        )

    def getPublicKeyForToken(self, token: str):
        try:
            header = jwt.get_unverified_header(token)

        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token header: {str(exc)}") from exc

        kid = header.get("kid")

        if not kid:
            raise ValueError(
                "Incoming token header is missing the required 'kid' parameter."
            )

        return self.getPublicKeyByKid(kid)


class AccessTokenVerifier:
    def __init__(
        self,
        env: EnvHandler,
        jwksProvider: JWKSProvider,
        logger: Logger | None = None,
    ) -> None:
        self.env = env
        self.jwksProvider = jwksProvider
        self.logger = logger or getLogger(__name__)

    def verifyAccessToken(self, token: str) -> AccessTokenPayload:
        try:
            publicKey = self.jwksProvider.getPublicKeyForToken(token)

            payload = jwt.decode(
                jwt=token,
                key=publicKey,
                algorithms=[self.env.JWT_ALGORITHM],
            )

            return AccessTokenPayload.model_validate(payload)

        except jwt.ExpiredSignatureError as exc:
            raise ValueError("Token has expired") from exc

        except jwt.InvalidTokenError as exc:
            raise ValueError(f"Invalid token: {str(exc)}") from exc
