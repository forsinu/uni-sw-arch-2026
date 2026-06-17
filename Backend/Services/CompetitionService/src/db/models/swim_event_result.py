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
    JSON,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class RaceResultStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    DNS = "DNS"
    DNF = "DNF"
    DSQ = "DSQ"


class SwimEventResult(Base):
    __tablename__ = "swim_event_results"

    __table_args__ = (
        CheckConstraint(
            '"finalTimeMs" IS NULL OR "finalTimeMs" > 0',
            name="ck_swim_event_results_final_time_positive",
        ),
        UniqueConstraint(
            "swimEventId",
            "federationId",
            name="uq_swim_event_results_event_federation_id",
        ),
        Index(
            "ix_swim_event_results_event_final_time",
            "swimEventId",
            "finalTimeMs",
        ),
    )

    federationId: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
    )

    splitTimesMs: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )

    finalTimeMs: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    status: Mapped[RaceResultStatus] = mapped_column(
        Enum(
            RaceResultStatus,
            native_enum=False,
            values_callable=lambda enumClass: [item.value for item in enumClass],
        ),
        nullable=False,
        default=RaceResultStatus.COMPLETED,
        index=True,
    )

    disqualificationReason: Mapped[str | None] = mapped_column(
        String(length=255),
        nullable=True,
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
        back_populates="results",
        foreign_keys=[swimEventId],
    )
