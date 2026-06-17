from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)

from src.db.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    __table_args__ = (
        Index(
            "ix_refresh_tokens_user_created_at",
            "userAccountId",
            "createdAt",
        ),
        Index(
            "ix_refresh_tokens_user_active_created_at",
            "userAccountId",
            "isActive",
            "createdAt",
        ),
        Index(
            "ix_refresh_tokens_user_active_expires_at",
            "userAccountId",
            "isActive",
            "expiresAt",
        ),
        Index(
            "ix_refresh_tokens_active_expires_at",
            "isActive",
            "expiresAt",
        ),
    )

    token: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
        nullable=False,
        index=True,
    )

    userAccountId: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    createdAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    expiresAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    rotatedAt: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    ipAddress: Mapped[Optional[str]] = mapped_column(
        String(length=45),
        nullable=True,
        default=None,
    )

    userAgent: Mapped[Optional[str]] = mapped_column(
        String(length=1024),
        nullable=True,
        default=None,
    )

    userAccount: Mapped["UserAccount"] = relationship(
        back_populates="refreshTokens",
        foreign_keys=[userAccountId],
    )
