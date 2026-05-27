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
    String,
    Uuid,
    func,
)


from src.db.models.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

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
        # default=True,
        index=True,
    )

    ipAddress: Mapped[Optional[str]] = mapped_column(
        String(length=45),
        nullable=False,
        default=None,
    )

    userAgent: Mapped[Optional[str]] = mapped_column(
        String(length=512),
        nullable=False,
        default=None,
    )

    userAccount: Mapped["UserAccount"] = relationship(
        back_populates="refreshTokens",
        foreign_keys=[userAccountId],
    )
