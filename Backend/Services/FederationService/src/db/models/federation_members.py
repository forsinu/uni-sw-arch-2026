from datetime import date, datetime
import enum
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


REFEREE_TEAM_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


class FederationRole(str, enum.Enum):
    ATHLETE = "ATH"
    COACH = "COA"
    REFEREE = "REF"
    TEAM_MANAGER = "MGR"


class FederationMember(Base):
    __tablename__ = "federation_members"

    __table_args__ = (
        UniqueConstraint(
            "fedRole",
            "teamId",
            "memberCode",
            name="uq_federation_members_role_team_member_code",
        ),
        Index(
            "ix_federation_members_team_role_active",
            "teamId",
            "fedRole",
            "isActive",
        ),
        Index(
            "ix_federation_members_last_first",
            "lastName",
            "firstName",
        ),
        CheckConstraint(
            'char_length("memberCode") >= 4',
            name="ck_federation_members_member_code_min_len",
        ),
    )

    federationId: Mapped[str] = mapped_column(
        String(length=128),
        nullable=False,
        unique=True,
        index=True,
    )

    fedRole: Mapped[FederationRole] = mapped_column(
        Enum(
            FederationRole,
            native_enum=False,
            values_callable=lambda enumClass: [item.value for item in enumClass],
        ),
        nullable=False,
        index=True,
    )

    teamId: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("swimming_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    memberCode: Mapped[str] = mapped_column(
        String(length=64),
        nullable=False,
        index=True,
    )

    firstName: Mapped[str] = mapped_column(
        String(length=100),
        nullable=False,
        index=True,
    )

    lastName: Mapped[str] = mapped_column(
        String(length=100),
        nullable=False,
        index=True,
    )

    isActive: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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
        back_populates="federationMembers",
        foreign_keys=[teamId],
    )

    @staticmethod
    def buildFederationId(
        role: FederationRole,
        teamId: uuid.UUID | None,
        memberCode: str,
    ) -> str:
        normalizedMemberCode = memberCode.strip().upper()

        if role == FederationRole.REFEREE:
            return f"{role.value}-{REFEREE_TEAM_ID}-{normalizedMemberCode}"

        if teamId is None:
            raise ValueError("teamId is required for non-referee federation members.")

        return f"{role.value}-{teamId}-{normalizedMemberCode}"
