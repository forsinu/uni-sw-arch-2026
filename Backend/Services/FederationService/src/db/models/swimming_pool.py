import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
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


class PoolType(str, enum.Enum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"


class PoolLength(int, enum.Enum):
    M25 = 25
    M50 = 50


class SwimmingPool(Base):
    __tablename__ = "swimming_pools"

    __table_args__ = (
        CheckConstraint(
            '"laneCount" > 0',
            name="ck_swimming_pools_lane_count_positive",
        ),
        CheckConstraint(
            'char_length("countryIso") = 2',
            name="ck_swimming_pools_country_iso_len",
        ),
        UniqueConstraint(
            "name",
            "city",
            "postalCode",
            "countryIso",
            name="uq_swimming_pools_name_city_postal_country",
        ),
        Index(
            "ix_swimming_pools_team_active",
            "teamId",
            "isActive",
        ),
        Index(
            "ix_swimming_pools_city_country",
            "city",
            "countryIso",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(length=128),
        nullable=False,
        index=True,
    )

    poolType: Mapped[PoolType] = mapped_column(
        Enum(
            PoolType,
            native_enum=False,
            values_callable=lambda enumClass: [item.value for item in enumClass],
        ),
        nullable=False,
        index=True,
    )

    poolLength: Mapped[PoolLength] = mapped_column(
        Enum(
            PoolLength,
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    laneCount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    streetAddress: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(length=64),
        nullable=False,
        index=True,
    )

    postalCode: Mapped[str] = mapped_column(
        String(length=16),
        nullable=False,
    )

    countryIso: Mapped[str] = mapped_column(
        String(length=2),
        nullable=False,
        index=True,
    )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    teamId: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swimming_teams.id", ondelete="SET NULL"),
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

    team: Mapped["SwimmingTeam | None"] = relationship(
        back_populates="swimmingPools",
        foreign_keys=[teamId],
    )
