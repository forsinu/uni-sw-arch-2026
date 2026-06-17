# src/db/repositories/federation_member.py

from collections.abc import Sequence
from datetime import date
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.federation_members import (
    FederationMember,
    FederationRole,
)


class FederationMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getMemberById(
        self,
        memberId: uuid.UUID,
        isActive: bool = False,
    ) -> FederationMember | None:
        query = select(FederationMember).where(FederationMember.id == memberId)

        if isActive:
            query = query.where(FederationMember.isActive == True)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getMemberByFederationId(
        self,
        federationId: str,
    ) -> FederationMember | None:
        query = select(FederationMember).where(
            FederationMember.federationId == federationId
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def getMemberByCode(
        self,
        memberCode: str,
        fedRole: FederationRole,
        teamId: uuid.UUID | None = None,
    ) -> FederationMember | None:
        query = select(FederationMember).where(
            FederationMember.memberCode == memberCode.upper(),
            FederationMember.fedRole == fedRole,
        )

        if teamId is not None:
            query = query.where(FederationMember.teamId == teamId)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listMembers(
        self,
        limit: int,
        offset: int,
        includeInactive: bool = False,
        teamId: uuid.UUID | None = None,
        fedRole: FederationRole | None = None,
    ) -> tuple[int, Sequence[FederationMember]]:
        countQuery = select(func.count()).select_from(FederationMember)
        dataQuery = select(FederationMember)

        if not includeInactive:
            countQuery = countQuery.where(FederationMember.isActive == True)
            dataQuery = dataQuery.where(FederationMember.isActive == True)

        if teamId is not None:
            countQuery = countQuery.where(FederationMember.teamId == teamId)
            dataQuery = dataQuery.where(FederationMember.teamId == teamId)

        if fedRole is not None:
            countQuery = countQuery.where(FederationMember.fedRole == fedRole)
            dataQuery = dataQuery.where(FederationMember.fedRole == fedRole)

        dataQuery = (
            dataQuery.order_by(
                FederationMember.lastName.asc(),
                FederationMember.firstName.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        members = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, members

    async def listMembersByTeamId(
        self,
        teamId: uuid.UUID,
        limit: int,
        offset: int,
        includeInactive: bool = False,
        fedRole: FederationRole | None = None,
    ) -> tuple[int, Sequence[FederationMember]]:
        return await self.listMembers(
            teamId=teamId,
            fedRole=fedRole,
            includeInactive=includeInactive,
            limit=limit,
            offset=offset,
        )

    async def listMembersByRole(
        self,
        fedRole: FederationRole,
        limit: int,
        offset: int,
        includeInactive: bool = False,
    ) -> tuple[int, Sequence[FederationMember]]:
        return await self.listMembers(
            fedRole=fedRole,
            includeInactive=includeInactive,
            limit=limit,
            offset=offset,
        )

    async def createMember(
        self,
        fedRole: FederationRole,
        teamId: uuid.UUID | None,
        memberCode: str,
        firstName: str,
        lastName: str,
        birth: date | None = None,
        isActive: bool = True,
    ) -> FederationMember:
        normalizedMemberCode = memberCode.strip().upper()

        federationId = FederationMember.buildFederationId(
            role=fedRole,
            teamId=teamId,
            memberCode=normalizedMemberCode,
        )

        member = FederationMember(
            federationId=federationId,
            fedRole=fedRole,
            teamId=teamId,
            birth=birth,
            memberCode=normalizedMemberCode,
            firstName=firstName,
            lastName=lastName,
            isActive=isActive,
        )

        self.session.add(member)
        await self.session.flush()

        return member

    async def updateMemberPersonalInfo(
        self,
        member: FederationMember,
        firstName: str | None = None,
        lastName: str | None = None,
        birth: date | None = None,
    ) -> FederationMember:
        if firstName is not None:
            member.firstName = firstName

        if lastName is not None:
            member.lastName = lastName

        if birth is not None:
            member.birth = birth

        await self.session.flush()

        return member

    async def updateMemberRoleAndTeam(
        self,
        member: FederationMember,
        fedRole: FederationRole,
        teamId: uuid.UUID | None,
    ) -> FederationMember:
        member.fedRole = fedRole
        member.teamId = teamId
        member.federationId = FederationMember.buildFederationId(
            role=fedRole,
            teamId=teamId,
            memberCode=member.memberCode,
        )

        await self.session.flush()

        return member

    async def assignMemberToTeam(
        self,
        member: FederationMember,
        teamId: uuid.UUID,
    ) -> FederationMember:
        member.teamId = teamId
        member.federationId = FederationMember.buildFederationId(
            role=member.fedRole,
            teamId=teamId,
            memberCode=member.memberCode,
        )

        await self.session.flush()

        return member

    async def detachMemberFromTeam(
        self,
        member: FederationMember,
    ) -> FederationMember:
        member.teamId = None
        member.federationId = FederationMember.buildFederationId(
            role=member.fedRole,
            teamId=None,
            memberCode=member.memberCode,
        )

        await self.session.flush()

        return member

    async def setMemberActiveStatus(
        self,
        member: FederationMember,
        isActive: bool,
    ) -> FederationMember:
        member.isActive = isActive

        await self.session.flush()

        return member

    async def deactivateMember(
        self,
        member: FederationMember,
    ) -> FederationMember:
        return await self.setMemberActiveStatus(
            member=member,
            isActive=False,
        )
