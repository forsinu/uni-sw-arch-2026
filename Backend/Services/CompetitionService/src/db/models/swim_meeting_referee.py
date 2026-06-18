from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Uuid,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class SwimMeetingReferee(Base):
    __tablename__ = "swim_meeting_referees"

    __table_args__ = (
        UniqueConstraint(
            "meetingId",
            "refereeFederationId",
            name="uq_swim_meeting_referees_meeting_referee",
        ),
        Index(
            "ix_swim_meeting_referees_meeting_id",
            "meetingId",
        ),
        Index(
            "ix_swim_meeting_referees_referee_user_account_id",
            "refereeFederationId",
        ),
    )

    meetingId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swim_meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    refereeFederationId: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
    )

    assignedBy: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        default=None,
    )

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    meeting: Mapped["SwimMeeting"] = relationship(
        back_populates="referees",
    )
