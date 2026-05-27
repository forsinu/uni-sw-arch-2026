from contextlib import asynccontextmanager
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from fastapi.exceptions import HTTPException
from fastapi import status


class ClientInfo(BaseModel):
    ip: Optional[str]
    ua: Optional[str]


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
