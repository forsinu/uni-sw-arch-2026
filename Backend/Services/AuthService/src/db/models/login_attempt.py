from datetime import datetime
from typing import Optional

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from sqlalchemy import (
    Index,
    Boolean,
    DateTime,
    String,
    func,
)

from src.db.models.base import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    __table_args__ = (
        Index(
            "ix_login_attempts_rate_limit",
            "usedEmail",
            "wasSuccessful",
            "attemptedAt",
        ),
        Index(
            "ix_login_attempts_email_attempted_at",
            "usedEmail",
            "attemptedAt",
        ),
        Index(
            "ix_login_attempts_attempted_at",
            "attemptedAt",
        ),
    )

    usedEmail: Mapped[str] = mapped_column(
        String(length=320),
        nullable=False,
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

    attemptedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    wasSuccessful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
