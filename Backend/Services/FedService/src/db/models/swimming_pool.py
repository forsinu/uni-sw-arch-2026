import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class PoolType(str, enum.Enum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"


class PoolLength(int, enum.Enum):
    M_25 = 25
    M_50 = 50


class SwimmingPool(Base):
    __tablename__ = "swimming_pools"

    name: Mapped[str] = mapped_column(
        String(length=128),
        nullable=False,
        unique=True,
    )

    lenPool: Mapped[PoolLength] = mapped_column(
        Enum(PoolLength, native_enum=False),
        nullable=False,
    )

    numbOfLane: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    streetAddr: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
    )

    postalCode: Mapped[str] = mapped_column(
        String(length=16),
        nullable=False,
    )

    countryIso: Mapped[str] = mapped_column(
        String(length=2),
        nullable=False,
    )

    teamId: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swimming_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    team: Mapped["SwimmingTeam | None"] = relationship(
        back_populates="swimmingPools",
        passive_deletes=True,
    )
