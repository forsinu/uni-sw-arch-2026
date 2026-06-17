from hmac import compare_digest
from pathlib import Path


class ServiceTokenHandler:
    def __init__(self, tokenPath: str) -> None:
        token = Path(tokenPath).read_text(encoding="utf-8").strip()

        if not token:
            raise RuntimeError("Service token file is empty.")

        self.token = token

    def verify(self, token: str) -> bool:
        return compare_digest(self.token, token)
