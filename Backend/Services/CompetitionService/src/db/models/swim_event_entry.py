from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class SwimEventEntry(Base):
    __tablename__ = "swim_event_entries"

    __table_args__ = (
        CheckConstraint(
            '"entryTimeMs" > 0',
            name="ck_swim_event_entries_entry_time_positive",
        ),
        UniqueConstraint(
            "swimEventId",
            "federationId",
            name="uq_swim_event_entries_event_federation_id",
        ),
        Index(
            "ix_swim_event_entries_event_time",
            "swimEventId",
            "entryTimeMs",
        ),
    )

    federationId: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
    )

    entryTimeMs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Usually the federationId of the team manager/coach/admin that created the entry.
    enteredBy: Mapped[str] = mapped_column(
        String(length=128),
        nullable=False,
        index=True,
    )

    swimEventId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swim_events.id", ondelete="CASCADE"),
        nullable=False,
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

    swimEvent: Mapped["SwimEvent"] = relationship(
        back_populates="entries",
        foreign_keys=[swimEventId],
    )
