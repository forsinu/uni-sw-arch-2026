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
    Index,
    String,
    Uuid,
    func,
)

from src.db.models.base import Base


class UserAccountRole(str, enum.Enum):
    DEFAULT = "DEFAULT"
    ADMIN = "ADMIN"


class UserAccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    ARCHIVED = "ARCHIVED"


class UserAccount(Base):
    __tablename__ = "user_accounts"

    __table_args__ = (
        Index(
            "ix_user_accounts_status_created_at",
            "accountStatus",
            "createdAt",
        ),
        Index(
            "ix_user_accounts_role_created_at",
            "userRole",
            "createdAt",
        ),
        Index(
            "ix_user_accounts_created_at",
            "createdAt",
        ),
    )

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

    federationId: Mapped[Optional[str]] = mapped_column(
        String(length=32),
        nullable=True,
        unique=True,
        default=None,
        index=True,
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

    __table_args__ = (
        Index(
            "ix_user_account_history_user_changed_at",
            "userAccountId",
            "changedAt",
        ),
        Index(
            "ix_user_account_history_changed_by_changed_at",
            "changedBy",
            "changedAt",
        ),
        Index(
            "ix_user_account_history_status_changed_at",
            "statusChangedTo",
            "changedAt",
        ),
    )

    userAccountId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    statusChangedTo: Mapped[UserAccountStatus] = mapped_column(
        Enum(UserAccountStatus, native_enum=False),
        nullable=False,
        index=True,
    )

    changedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    changedBy: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(length=500),
        nullable=True,
    )

    userAccount: Mapped["UserAccount"] = relationship(
        back_populates="statusHistory",
        foreign_keys=[userAccountId],
    )

    changedByUser: Mapped[Optional["UserAccount"]] = relationship(
        foreign_keys=[changedBy],
    )
