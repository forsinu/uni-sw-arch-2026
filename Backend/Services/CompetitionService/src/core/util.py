from contextlib import asynccontextmanager
from typing import Optional
from pydantic import BaseModel, model_validator

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


from fastapi import status, HTTPException

from src.db.models.swim_event import RaceDistance, RaceStroke

VALID_EVENTS: dict[RaceStroke, set[RaceDistance]] = {
    RaceStroke.FREESTYLE: set(RaceDistance),
    RaceStroke.MEDLEY: {
        RaceDistance.M200,
        RaceDistance.M400,
    },
    RaceStroke.BACKSTROKE: {
        RaceDistance.M50,
        RaceDistance.M100,
        RaceDistance.M200,
    },
    RaceStroke.BREASTSTROKE: {
        RaceDistance.M50,
        RaceDistance.M100,
        RaceDistance.M200,
    },
    RaceStroke.BUTTERFLY: {
        RaceDistance.M50,
        RaceDistance.M100,
        RaceDistance.M200,
    },
}


class PaginationMetadata(BaseModel):
    totalRecords: int
    limit: int
    offset: int
    hasMore: bool


@asynccontextmanager
async def handleDbOp(
    session: AsyncSession,
    errorMsg: str = "Internal Server Error.",
    integrityMsg: Optional[str] = None,
):
    try:
        yield

    except IntegrityError as i:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=integrityMsg if integrityMsg else "Relation Integrity Error.",
        )

    except SQLAlchemyError as e:
        await session.rollback()
        # TODO: Add Logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=errorMsg,
        )


class SwimEventModel(BaseModel):
    distance: RaceDistance
    stroke: RaceStroke

    @model_validator(mode="after")
    def validate_event_combinations(self) -> "SwimEventModel":
        allowedDist = VALID_EVENTS.get(self.stroke, set())

        if self.distance not in allowedDist:
            raise ValueError(
                f"Invalid race configuration: {self.distance.value}m "
                f"{self.stroke.value} is not an officially recognized swim event."
            )

        return self
