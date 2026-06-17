from __future__ import annotations

from datetime import date, datetime
import enum
import uuid

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class SwimMeetingStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    ENTRIES_OPEN = "ENTRIES_OPEN"
    ENTRIES_CLOSED = "ENTRIES_CLOSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MeetingPoolLength(int, enum.Enum):
    M25 = 25
    M50 = 50


class SwimMeeting(Base):
    __tablename__ = "swim_meetings"

    __table_args__ = (
        CheckConstraint(
            '"poolLength" IN (25, 50)',
            name="ck_swim_meetings_pool_length",
        ),
        CheckConstraint(
            '"entriesOpenAt" < "entriesCloseAt"',
            name="ck_swim_meetings_entries_window",
        ),
        CheckConstraint(
            '"startDate" <= "endDate"',
            name="ck_swim_meetings_date_range",
        ),
        UniqueConstraint(
            "name",
            "startDate",
            name="uq_swim_meetings_name_start_date",
        ),
        Index(
            "ix_swim_meetings_status_start_date",
            "status",
            "startDate",
        ),
        Index(
            "ix_swim_meetings_pool_start_date",
            "swimmingPoolId",
            "startDate",
        ),
        Index(
            "ix_swim_meetings_organizer_start_date",
            "organizerTeamId",
            "startDate",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
    )

    poolLength: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    status: Mapped[SwimMeetingStatus] = mapped_column(
        Enum(
            SwimMeetingStatus,
            native_enum=False,
            values_callable=lambda enumClass: [item.value for item in enumClass],
        ),
        nullable=False,
        default=SwimMeetingStatus.UPCOMING,
        index=True,
    )

    entriesOpenAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    entriesCloseAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    startDate: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    endDate: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # External reference to Federation Service team.
    organizerTeamId: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )

    # External reference to Federation Service swimming pool.
    swimmingPoolId: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updatedAt: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        onupdate=func.now(),
    )

    swimEvents: Mapped[list["SwimEvent"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SwimEvent.startAt",
    )
