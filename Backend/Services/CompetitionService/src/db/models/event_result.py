import enum
from typing import Optional
import uuid


from sqlalchemy import (
    Enum,
    Float,
    Uuid,
    String,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

# from src.db.models.swim_event import SwimEvent
from src.db.models.base import Base


class RaceResultStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    DNS = "DNS"  # Did Not Start
    DNF = "DNF"  # Did Not Finish
    DSQ = "DSQ"  # Disqualified


class SwimEventResult(Base):
    __tablename__ = "swim_event_results"

    # Federation ID
    federationId: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        index=True,
    )

    splits: Mapped[list[float]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    finalTime: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[RaceResultStatus] = mapped_column(
        Enum(RaceResultStatus, native_enum=False),
        default=RaceResultStatus.COMPLETED,
        nullable=False,
    )

    swimEventId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swim_events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    swimEvent: Mapped["SwimEvent"] = relationship(
        back_populates="results",
        foreign_keys=[swimEventId],
    )
