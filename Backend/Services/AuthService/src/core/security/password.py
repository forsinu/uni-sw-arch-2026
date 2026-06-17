import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError


class PasswordService:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.passwordHasher = PasswordHasher()

    def hashPassword(self, password: str) -> str:
        return self.passwordHasher.hash(password)

    def verifyPassword(self, hashedPassword: str, plainPassword: str) -> bool:
        try:
            return self.passwordHasher.verify(
                hash=hashedPassword,
                password=plainPassword,
            )

        except VerifyMismatchError:
            return False

        except VerificationError:
            self.logger.warning("Password hash verification failed")
            return False

    def needsRehash(self, hashedPassword: str) -> bool:
        return self.passwordHasher.check_needs_rehash(hashedPassword)
