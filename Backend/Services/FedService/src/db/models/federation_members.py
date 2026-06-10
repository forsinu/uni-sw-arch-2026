from datetime import date
import enum
from typing import Optional
import uuid

from sqlalchemy import Date, Enum, ForeignKey, String
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

    federationId: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    fedRole: Mapped[FederationRole] = mapped_column(
        Enum(FederationRole, native_enum=False),
        nullable=False,
        index=True,
    )

    teamId: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("swimming_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    memberCode: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    firstName: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    lastName: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    isActive: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    team: Mapped["SwimmingTeam"] = relationship(
        back_populates="federationMembers",
        foreign_keys=[teamId],
        passive_deletes=True,
    )

    # __table_args__ = (
    #     UniqueConstraint(
    #         "teamId",
    #         "memberCode",
    #         name="uq_federation_members_team_id_member_code",
    #     ),
    #     Index(
    #         "ix_federation_members_team_id_role",
    #         "teamId",
    #         "role",
    #     ),
    # )

    @staticmethod
    def buildFederationId(
        role: FederationRole,
        teamId: uuid.UUID,
        memberCode: str,
    ) -> str:
        if role == FederationRole.REFEREE:
            return f"{role.value}-{REFEREE_TEAM_ID}-{memberCode}"

        return f"{role.value}-{teamId}-{memberCode}"
