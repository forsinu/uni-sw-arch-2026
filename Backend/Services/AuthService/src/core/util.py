from contextlib import asynccontextmanager
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


@asynccontextmanager
async def handleDbOp(session: AsyncSession, errorMsg: str):
    try:
        yield

    except SQLAlchemyError as e:
        await session.rollback()
        print(e)
        # TODO: Add Logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=errorMsg,
        )
