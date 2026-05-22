from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI

from src.api.v1.api import api as apiV1

from src.api.dependencies import db


async def addAdmin():
    from sqlalchemy.dialects.postgresql import insert
    from src.db.model import UserAccount, UserAccountRole
    from src.api.dependencies import dbHandler
    from argon2 import PasswordHasher

    ph = PasswordHasher()

    # 1. Properly get the session using anext() on the async generator
    session_generator = dbHandler()
    session = await anext(session_generator)

    # 2. Execute the insert asynchronously
    passwd = ph.hash("adminadminadmin")
    stmt = insert(UserAccount).values(
        email="admin@admin.com",
        password=passwd,
        userRole=UserAccountRole.ADMIN_ACCOUNT,
    )

    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=[UserAccount.email],
        set_={
            "password": passwd,
            "updatedAt": datetime.now(timezone.utc),
        },
    )

    await session.execute(upsert_stmt)

    # 3. Commit the transaction
    await session.commit()
    print("Startup System: Admin account successfully synchronized.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.initModel()

    await addAdmin()

    yield

    await db.closeConnection()


app = FastAPI(lifespan=lifespan)
app.include_router(apiV1, prefix="/api/v1")
