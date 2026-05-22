from contextlib import asynccontextmanager
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class ClientInfo(BaseModel):
    ip: str
    userAgent: str


@asynccontextmanager
async def handleDbOp(session: AsyncSession, errorMsg: str):
    try:
        yield

    except IntegrityError as i:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entity already exists in the database.",
        )

    except SQLAlchemyError as e:
        await session.rollback()
        # print(e)
        # TODO: Add Logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=errorMsg,
        )
