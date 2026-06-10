from contextlib import asynccontextmanager
from typing import Optional, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement


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

    except IntegrityError:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=integrityMsg if integrityMsg else "Relation Integrity Error.",
        )

    except SQLAlchemyError:
        await session.rollback()
        # TODO: Add Logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=errorMsg,
        )


ModelT = TypeVar("ModelT")


async def getOneOr404(
    session: AsyncSession,
    model: type[ModelT],
    *whereClauses: ColumnElement[bool],
    errorMsg: str = "Could not retrieve resource.",
    notFoundMsg: str = "Resource not found.",
) -> ModelT:
    """
    Example:
        team = await getOneOr404(
            db,
            SwimmingTeam,
            SwimmingTeam.id == teamId,
            errorMsg="Could not retrieve swimming team.",
            notFoundMsg="Swimming team not found.",
        )
    """
    async with handleDbOp(
        session=session,
        errorMsg=errorMsg,
    ):
        result = await session.execute(select(model).where(*whereClauses))

    entity = result.scalar_one_or_none()

    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=notFoundMsg,
        )

    return entity
