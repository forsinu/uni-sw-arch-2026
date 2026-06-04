import enum
import uuid


from sqlalchemy import (
    Enum,
    Float,
    String,
    Uuid,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)


# from src.db.models.swim_event import SwimEvent
from src.db.models.base import Base


class SwimEventEntry(Base):
    __tablename__ = "swim_event_entries"

    federationId: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        index=True,
    )

    entryTime: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    enteredBy: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        index=True,
    )

    swimEventId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swim_events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    swimEvent: Mapped["SwimEvent"] = relationship(
        back_populates="entries",
        foreign_keys=[swimEventId],
    )
