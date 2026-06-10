from datetime import date, datetime
import enum
from typing import Optional
import uuid
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

# FIXED: Imported enums from swim_event instead of copying and pasting them here
from src.db.models.swim_event import SwimEvent


class SwimMeetingStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    ENTRIES_OPEN = "ENTRIES_OPEN"
    ENTRIES_CLOSED = "ENTRIES_CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SwimMeeting(Base):
    __tablename__ = "swim_meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
    )

    poolLength: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    status: Mapped[SwimMeetingStatus] = mapped_column(
        Enum(SwimMeetingStatus, native_enum=False),
        nullable=False,
        index=True,
        default=SwimMeetingStatus.UPCOMING,
    )

    entriesOpenAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    entriesCloseAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    startAt: Mapped[date] = mapped_column(Date, nullable=False)

    endAt: Mapped[date] = mapped_column(Date, nullable=False)

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # From Federation Service
    organizedBy: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )

    # From Federation Service
    swimmingPoolId: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )

    swimEvents: Mapped[list["SwimEvent"]] = relationship(
        # default_factory=list,
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="SwimEvent.startAt.asc()",
    )
