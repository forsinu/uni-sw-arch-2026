import base64
import logging
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from src.core.environment import EnvHandler


class RSAKeyProvider:
    def __init__(
        self,
        env: EnvHandler,
        logger: logging.Logger,
    ) -> None:

        self.env = env
        self.logger = logger

        self.privateKeyPem: bytes | None = None
        self.publicKeyPem: bytes | None = None
        self.cachedJWK: dict | None = None

    async def initialize(self) -> None:
        self.logger.info("Loading JWT RSA keys")

        privatePath = Path(self.env.PRIVATE_KEY_PATH)
        publicPath = Path(self.env.PUBLIC_KEY_PATH)

        if not privatePath.exists():
            raise RuntimeError(f"Missing private JWT key: {privatePath}")

        if not publicPath.exists():
            raise RuntimeError(f"Missing public JWT key: {publicPath}")

        self.privateKeyPem = privatePath.read_bytes()
        self.publicKeyPem = publicPath.read_bytes()
        self.cachedJWK = self._generateJWK()

        self.logger.info("JWT RSA keys loaded successfully")

    def _ensureInitialized(self) -> None:
        if self.privateKeyPem is None or self.publicKeyPem is None:
            raise RuntimeError("RSAKeyProvider has not been initialized")

        if self.cachedJWK is None:
            raise RuntimeError("JWK has not been initialized")

    def _intToBase64Url(self, num: int) -> str:
        numBytes = num.to_bytes(
            (num.bit_length() + 7) // 8,
            byteorder="big",
        )

        return base64.urlsafe_b64encode(numBytes).rstrip(b"=").decode("utf-8")

    def _generateJWK(self) -> dict:
        if self.publicKeyPem is None:
            raise RuntimeError("Public key has not been loaded")

        try:
            keyObj = serialization.load_pem_public_key(
                self.publicKeyPem,
                backend=default_backend(),
            )

            publicNumbers = keyObj.public_numbers()

            return {
                "kty": "RSA",
                "use": "sig",
                "key_ops": ["verify"],
                "alg": self.env.JWT_ALGORITHM,
                "kid": self.env.JWT_KEY_ID,
                "n": self._intToBase64Url(publicNumbers.n),
                "e": self._intToBase64Url(publicNumbers.e),
            }

        except Exception as exc:
            raise RuntimeError("Failed to generate JWK from public key") from exc

    def getPrivateKey(self) -> bytes:
        self._ensureInitialized()
        assert self.privateKeyPem is not None
        return self.privateKeyPem

    def getPublicKey(self) -> bytes:
        self._ensureInitialized()
        assert self.publicKeyPem is not None
        return self.publicKeyPem

    def getJWKS(self) -> dict:
        self._ensureInitialized()
        assert self.cachedJWK is not None
        return {"keys": [self.cachedJWK]}
