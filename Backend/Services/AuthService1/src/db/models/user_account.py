from datetime import datetime, timezone
import enum
from typing import Optional
import uuid

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Uuid,
    func,
)


from src.db.models.base import Base


class UserAccountRole(str, enum.Enum):
    DEFAULT = "DEFAULT"
    ADMIN = "ADMIN"


class UserAccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"  # Operational Account
    SUSPENDED = "SUSPENDED"  # Temporary Restrictions
    BANNED = "BANNED"  # Permanent Restrictions
    ARCHIVED = "ARCHIVED"  # Soft-Deletion


class UserAccount(Base):
    __tablename__ = "user_accounts"

    email: Mapped[str] = mapped_column(
        String(length=320),
        unique=True,
        nullable=False,
        index=True,
    )

    password: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )

    userRole: Mapped[UserAccountRole] = mapped_column(
        Enum(UserAccountRole, native_enum=False),
        nullable=False,
        default=UserAccountRole.DEFAULT,
    )

    # Remember to set the federationID to RRR-XXXXXXXXX...X (28 bytes)
    federationId: Mapped[Optional[str]] = mapped_column(
        String(length=32),
        nullable=True,
        unique=True,
        default=None,
    )

    accountStatus: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus, native_enum=False),
        default=UserAccountStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updatedAt: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
        default=None,
    )

    refreshTokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="userAccount",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    statusHistory: Mapped[list["UserAccountHistory"]] = relationship(
        back_populates="userAccount",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="UserAccountHistory.userAccountId",
    )


class UserAccountHistory(Base):
    __tablename__ = "user_account_history"

    userAccountId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    statusChangedTo: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus, native_enum=False),
        nullable=False,
    )

    changedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    changedBy: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(length=500),
        nullable=True,
    )

    userAccount: Mapped["UserAccount"] = relationship(
        back_populates="statusHistory",
        foreign_keys=[userAccountId],
    )
