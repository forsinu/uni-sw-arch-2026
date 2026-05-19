from datetime import datetime, timezone
import enum
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
    __tablename__ = "UserAccounts"

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

    federationID: Mapped[str] = mapped_column(
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

    isDisabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    disabledAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    updatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.now(timezone.utc),
        default=None,
    )

    refreshTokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="userAccount",
        cascade="all, delete-orphan",
    )


class RefreshToken(Base):
    __tablename__ = "refreshTokens"

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

    rotatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    userAccount: Mapped[UserAccount] = relationship(back_populates="refreshTokens")


class LoginAttempt(Base):
    __tablename__ = "loginAttempts"

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
