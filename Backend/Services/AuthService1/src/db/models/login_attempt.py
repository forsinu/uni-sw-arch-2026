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
            "wasSuccessfull",
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
        nullable=False,
        default=None,
    )

    userAgent: Mapped[Optional[str]] = mapped_column(
        String(length=512),
        nullable=False,
        default=None,
    )

    attemptedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    wasSuccessfull: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
