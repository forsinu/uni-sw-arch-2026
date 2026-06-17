from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class SwimmingTeam(Base):
    __tablename__ = "swimming_teams"

    __table_args__ = (Index("ix_swimming_teams_active_name", "isActive", "name"),)

    name: Mapped[str] = mapped_column(
        String(length=128),
        nullable=False,
        unique=True,
        index=True,
    )

    shortName: Mapped[str | None] = mapped_column(
        String(length=16),
        nullable=True,
        unique=True,
        index=True,
    )

    # federationCode: Mapped[str | None] = mapped_column(
    #     String(length=255),
    #     nullable=True,
    #     unique=True,
    #     index=True,
    # )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    federationMembers: Mapped[list["FederationMember"]] = relationship(
        back_populates="team",
        passive_deletes=True,
    )

    swimmingPools: Mapped[list["SwimmingPool"]] = relationship(
        back_populates="team",
        passive_deletes=True,
    )
