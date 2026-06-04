# This class should be in Federation Service
# Any SwimmingPool where swimming meets can be held
# must be registered to the Federation

import enum
import uuid

from sqlalchemy import Enum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.swim_meeting import SwimMeeting
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

    # Information about Location
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

    societyId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )

    meetings: Mapped[list["SwimMeeting"]] = relationship(
        back_populates="swimmingPool",
        cascade="save-update, merge",
    )
