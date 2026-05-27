import uuid

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from sqlalchemy import Uuid


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid7,
    )
