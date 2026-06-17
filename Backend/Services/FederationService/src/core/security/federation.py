# src/core/security/federation.py

import re
import uuid
import secrets
import string
from logging import Logger, getLogger

from src.core.security.models import AccessTokenPayload
from src.db.models.federation_members import FederationRole


class FederationIdentityHandler:
    MEMBER_CODE_ALPHABET = string.ascii_uppercase + string.digits
    FED_ID_PATTERN = re.compile(
        r"^(.+?)-"
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
        r"-(.*)$"
    )

    def __init__(
        self,
        logger: Logger | None = None,
    ) -> None:
        self.logger = logger or getLogger(__name__)

    def extractFedFields(
        self,
        token: AccessTokenPayload,
    ) -> tuple[FederationRole, uuid.UUID]:
        fedId = token.fed

        if not fedId:
            raise ValueError("Provided federation ID is missing.")

        match = self.FED_ID_PATTERN.match(fedId)

        if not match:
            raise ValueError("Provided federation ID structure is incorrect.")

        rolePrefix = match.group(1)
        teamIdValue = match.group(2)

        try:
            role = FederationRole(rolePrefix)

        except ValueError as exc:
            raise ValueError(
                f"Invalid federation ID structure: '{rolePrefix}' "
                f"is not a recognized federation role."
            ) from exc

        try:
            teamId = uuid.UUID(teamIdValue)

        except ValueError as exc:
            raise ValueError(
                f"Invalid federation ID structure: '{teamIdValue}' "
                f"is not a valid UUID string."
            ) from exc

        return role, teamId

    def generateMemberCode(self, length: int = 12) -> str:
        return "".join(secrets.choice(self.MEMBER_CODE_ALPHABET) for _ in range(length))
