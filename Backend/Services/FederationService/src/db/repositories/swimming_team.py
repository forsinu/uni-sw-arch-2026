from collections.abc import Sequence
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swimming_team import SwimmingTeam


class SwimmingTeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getTeamById(
        self, teamId: uuid.UUID, active: bool = False
    ) -> SwimmingTeam | None:
        query = select(SwimmingTeam).where(SwimmingTeam.id == teamId)

        if active:
            query = query.where(SwimmingTeam.isActive == True)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getTeamByName(self, name: str) -> SwimmingTeam | None:
        query = select(SwimmingTeam).where(SwimmingTeam.name == name)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getTeamByShortName(self, shortName: str) -> SwimmingTeam | None:
        query = select(SwimmingTeam).where(SwimmingTeam.shortName == shortName)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listTeams(
        self,
        limit: int,
        offset: int,
        includeInactive: bool = False,
    ) -> tuple[int, Sequence[SwimmingTeam]]:
        countQuery = select(func.count()).select_from(SwimmingTeam)
        dataQuery = select(SwimmingTeam)

        if not includeInactive:
            countQuery = countQuery.where(SwimmingTeam.isActive == True)
            dataQuery = dataQuery.where(SwimmingTeam.isActive == True)

        dataQuery = (
            dataQuery.order_by(SwimmingTeam.name.asc()).offset(offset).limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        teams = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, teams

    async def createTeam(
        self,
        name: str,
        shortName: str | None = None,
        isActive: bool = True,
    ) -> SwimmingTeam:
        team = SwimmingTeam(
            name=name,
            shortName=shortName,
            isActive=isActive,
        )

        self.session.add(team)
        await self.session.flush()

        return team

    async def updateTeamInfo(
        self,
        team: SwimmingTeam,
        name: str | None = None,
        shortName: str | None = None,
        isActive: bool | None = None,
    ) -> SwimmingTeam:
        if name is not None:
            team.name = name

        if shortName is not None:
            team.shortName = shortName

        if isActive and isActive != team.isActive:
            team.isActive = isActive

        await self.session.flush()

        return team
