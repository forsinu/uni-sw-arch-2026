# src/db/repositories/swimming_pool.py

from collections.abc import Sequence
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.swimming_pool import PoolLength, PoolType, SwimmingPool


class SwimmingPoolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def getPoolById(self, poolId: uuid.UUID) -> SwimmingPool | None:
        query = select(SwimmingPool).where(SwimmingPool.id == poolId)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def listPools(
        self,
        limit: int,
        offset: int,
        city: str | None = None,
        countryIso: str | None = None,
        teamId: uuid.UUID | None = None,
        includeInactive: bool = False,
    ) -> tuple[int, Sequence[SwimmingPool]]:
        countQuery = select(func.count()).select_from(SwimmingPool)
        dataQuery = select(SwimmingPool)

        if not includeInactive:
            countQuery = countQuery.where(SwimmingPool.isActive == True)
            dataQuery = dataQuery.where(SwimmingPool.isActive == True)

        if city is not None:
            countQuery = countQuery.where(SwimmingPool.city == city)
            dataQuery = dataQuery.where(SwimmingPool.city == city)

        if countryIso is not None:
            normalizedCountryIso = countryIso.upper()

            countQuery = countQuery.where(
                SwimmingPool.countryIso == normalizedCountryIso
            )
            dataQuery = dataQuery.where(SwimmingPool.countryIso == normalizedCountryIso)

        if teamId is not None:
            countQuery = countQuery.where(SwimmingPool.teamId == teamId)
            dataQuery = dataQuery.where(SwimmingPool.teamId == teamId)

        dataQuery = (
            dataQuery.order_by(SwimmingPool.name.asc()).offset(offset).limit(limit)
        )

        totalRecords = (await self.session.execute(countQuery)).scalar_one()
        pools = (await self.session.execute(dataQuery)).scalars().all()

        return totalRecords, pools

    async def createPool(
        self,
        name: str,
        poolType: PoolType,
        poolLength: PoolLength,
        laneCount: int,
        streetAddress: str,
        city: str,
        postalCode: str,
        countryIso: str,
        teamId: uuid.UUID | None = None,
    ) -> SwimmingPool:
        pool = SwimmingPool(
            name=name,
            poolType=poolType,
            poolLength=poolLength,
            laneCount=laneCount,
            streetAddress=streetAddress,
            city=city,
            postalCode=postalCode,
            countryIso=countryIso.upper(),
            teamId=teamId,
        )

        self.session.add(pool)
        await self.session.flush()

        return pool

    async def updatePool(
        self,
        pool: SwimmingPool,
        name: str | None = None,
        poolType: PoolType | None = None,
        poolLength: PoolLength | None = None,
        laneCount: int | None = None,
        streetAddress: str | None = None,
        city: str | None = None,
        postalCode: str | None = None,
        countryIso: str | None = None,
        teamId: uuid.UUID | None = None,
        isActive: bool | None = None,
    ) -> SwimmingPool:
        if name is not None:
            pool.name = name

        if poolType is not None:
            pool.poolType = poolType

        if poolLength is not None:
            pool.poolLength = poolLength

        if laneCount is not None:
            pool.laneCount = laneCount

        if streetAddress is not None:
            pool.streetAddress = streetAddress

        if city is not None:
            pool.city = city

        if postalCode is not None:
            pool.postalCode = postalCode

        if countryIso is not None:
            pool.countryIso = countryIso.upper()

        if teamId is not None:
            pool.teamId = teamId

        if isActive is not None:
            pool.isActive = isActive

        await self.session.flush()

        return pool

    async def deactivatePool(self, pool: SwimmingPool) -> SwimmingPool:
        pool.isActive = False

        await self.session.flush()
        return pool
