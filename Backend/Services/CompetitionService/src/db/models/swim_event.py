from __future__ import annotations

from datetime import datetime
import enum
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    __table_args__ = (
        CheckConstraint(
            "distance IN (50, 100, 200, 400, 800, 1500)",
            name="ck_swim_events_distance",
        ),
        UniqueConstraint(
            "meetingId",
            "distance",
            "stroke",
            "gender",
            name="uq_swim_events_meeting_distance_stroke_gender",
        ),
        Index(
            "ix_swim_events_meeting_start",
            "meetingId",
            "startAt",
        ),
        Index(
            "ix_swim_events_program",
            "distance",
            "stroke",
            "gender",
        ),
    )

    distance: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    stroke: Mapped[RaceStroke] = mapped_column(
        Enum(
            RaceStroke,
            native_enum=False,
            values_callable=lambda enumClass: [item.value for item in enumClass],
        ),
        nullable=False,
        index=True,
    )

    gender: Mapped[RaceGender] = mapped_column(
        Enum(
            RaceGender,
            native_enum=False,
            values_callable=lambda enumClass: [item.value for item in enumClass],
        ),
        nullable=False,
        index=True,
    )

    meetingId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swim_meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    startAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    meeting: Mapped["SwimMeeting"] = relationship(
        back_populates="swimEvents",
        foreign_keys=[meetingId],
    )

    entries: Mapped[list["SwimEventEntry"]] = relationship(
        back_populates="swimEvent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    results: Mapped[list["SwimEventResult"]] = relationship(
        back_populates="swimEvent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
