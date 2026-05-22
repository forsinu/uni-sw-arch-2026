from datetime import datetime, timezone
import enum
from typing import Optional
import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Uuid


class UserAccountRole(str, enum.Enum):
    DEFAULT_ACCOUNT = "DEFAULT_ACCOUNT"
    ADMIN_ACCOUNT = "ADMIN_ACCOUNT"


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid7,
    )


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
        default=UserAccountRole.DEFAULT_ACCOUNT,
    )

    federationId: Mapped[Optional[str]] = mapped_column(
        String(
            length=32
        ),  # Remember to set the federationID to RRR-XXXXXXXXX...X (28 bytes)
        nullable=True,
        unique=True,
        default=None,
    )

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    disabledAt: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
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
    )

    createdBy: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    updatedBy: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
        index=True,
        nullable=False,
    )

    userAccountId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(UserAccount.id, ondelete="CASCADE"),
        nullable=False,
    )

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    expiresAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    rotatedAt: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    ipAddress: Mapped[str] = mapped_column(
        String(length=45),
        nullable=False,
        default="Unknown",
    )

    userAgent: Mapped[str] = mapped_column(
        String(length=512),
        nullable=False,
        default="Unknown",
    )

    userAccount: Mapped[UserAccount] = relationship(
        back_populates="refreshTokens",
        foreign_keys=[userAccountId],
    )


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    usedEmail: Mapped[str] = mapped_column(
        String(length=320),
        nullable=False,
        index=True,
    )

    ipAddress: Mapped[str] = mapped_column(
        String(length=45),
        nullable=False,
        default="Unknown",
    )

    userAgent: Mapped[str] = mapped_column(
        String(length=512),
        nullable=False,
        default="Unknown",
    )

    attemptedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    wasSuccessfull: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class ResetPasswdAttempt(Base):
    __tablename__ = "reset_password_attempts"

    userAccountId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(UserAccount.id, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attemptedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    wasSuccessfull: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
