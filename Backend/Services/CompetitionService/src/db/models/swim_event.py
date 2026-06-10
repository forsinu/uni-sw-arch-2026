from datetime import datetime
import enum
import uuid


from sqlalchemy import (
    DateTime,
    Enum,
    Uuid,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.db.models.event_entries import SwimEventEntry
from src.db.models.event_result import SwimEventResult

# from src.db.models.swim_meeting import SwimMeeting
from src.db.models.base import Base


class RaceDistance(int, enum.Enum):
    M50 = 50
    M100 = 100
    M200 = 200
    M400 = 400
    M800 = 800
    M1500 = 1500


class RaceStroke(str, enum.Enum):
    FREESTYLE = "FREESTYLE"
    BACKSTROKE = "BACKSTROKE"
    BREASTSTROKE = "BREASTSTROKE"
    BUTTERFLY = "BUTTERFLY"
    MEDLEY = "MEDLEY"


class RaceGender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class SwimEvent(Base):
    __tablename__ = "swim_events"

    distance: Mapped[RaceDistance] = mapped_column(
        Enum(RaceDistance, native_enum=False),
        nullable=False,
    )

    stroke: Mapped[RaceStroke] = mapped_column(
        Enum(RaceStroke, native_enum=False),
        nullable=False,
    )

    gender: Mapped[RaceGender] = mapped_column(
        Enum(RaceGender, native_enum=False),
        nullable=False,
        index=True,
    )

    meetingId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swim_meetings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    startAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    entries: Mapped[list["SwimEventEntry"]] = relationship(
        back_populates="swimEvent",
        cascade="all, delete-orphan",
    )

    meeting: Mapped["SwimMeeting"] = relationship(
        back_populates="swimEvents",
        foreign_keys=[meetingId],
    )

    results: Mapped[list["SwimEventResult"]] = relationship(
        back_populates="swimEvent",
        cascade="all, delete-orphan",
    )
