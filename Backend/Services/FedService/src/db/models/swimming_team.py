import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class SwimmingTeam(Base):
    __tablename__ = "swimming_teams"

    name: Mapped[str] = mapped_column(
        String(length=128),
        nullable=False,
        unique=True,
        index=True,
    )

    shortName: Mapped[str | None] = mapped_column(
        String(length=32),
        nullable=True,
        unique=True,
        index=True,
    )

    federationCode: Mapped[str | None] = mapped_column(
        String(length=64),
        nullable=True,
        unique=True,
        index=True,
    )

    isActive: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    federationMembers: Mapped[list["FederationMember"]] = relationship(
        back_populates="team",
        passive_deletes=True,
    )

    swimmingPools: Mapped[list["SwimmingPool"]] = relationship(
        back_populates="team",
        passive_deletes=True,
    )
