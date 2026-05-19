from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Cookie, Depends, HTTPException, Header, Response, status

from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.util import handleDbOp
from src.core.security import SecurityHandler
from src.db.model import LoginAttempt, RefreshToken, UserAccount
from src.schema.auth import LoginReq, LogoutReq, RegistrationReq, TokenResp
from src.api.dependencies import dbHandler, secHandler, tokenHandler

router = APIRouter()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def registration(
    user: RegistrationReq,
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
):
    account = UserAccount(
        email=user.email,
        password=sec.hashPassword(user.password),
    )

    db.add(account)

    try:
        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    except SQLAlchemyError as e:
        await db.rollback()
        # TODO: Log the actual error (e) to your server logs here
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration.",
        )


@router.post(
    "/login",
    response_model=TokenResp,
    status_code=status.HTTP_200_OK,
)
async def login(
    # === Request Body Model
    credentials: LoginReq,
    # === Response
    response: Response,
    # === Dependecies
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    # === Headers
    user_agent: Annotated[Optional[str], Header()] = None,
    x_forwarded_for: Annotated[Optional[str], Header()] = None,
):
    clientIp = "Unknown"
    if x_forwarded_for:
        clientIp = x_forwarded_for.split(",")[0].strip()

    userAgent = user_agent or "Unknown"

    loginAttempt = LoginAttempt(
        usedEmail=credentials.email,
        ipAddress=clientIp,
        userAgent=userAgent,
    )

    query = await db.execute(
        select(UserAccount).where(UserAccount.email == credentials.email)
    )

    result = query.scalar_one_or_none()

    if result:
        passwdMatches = sec.verifyPassword(result.password, credentials.password)
    else:
        # SECURITY: run dummy password verification in order to
        # maintain the response duration uniform
        sec.verifyPassword(
            "$argon2id$v=19$m=65536,t=3,p=4$dHVtbXlkdW1teWR1bW15$dummyhash",
            credentials.password,
        )
        passwdMatches = False

    if not passwdMatches:
        async with handleDbOp(db, "Internal server error during login."):
            db.add(loginAttempt)
            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    loginAttempt.wasSuccessfull = True

    accessToken = sec.generateAccessToken(
        userId=result.id,
        role=result.userRole,
        fed=result.federationID,
    )

    tmpRt = sec.generateRandomToken()
    refreshToken = RefreshToken(
        token=tmpRt["token"],
        userAccountId=result.id,
        expiresAt=tmpRt["exp"],
    )

    async with handleDbOp(db, "Internal server error during sign in."):
        db.add(loginAttempt)
        db.add(refreshToken)

        await db.commit()

    response.set_cookie(
        key="rt",
        value=refreshToken.token,
        max_age=sec.env.RT_EXP_MIN * 60,
        httponly=True,
        # secure=True,
        samesite="lax",
    )

    return TokenResp(at=accessToken, tt="bearer")


@router.post("/refresh", response_model=TokenResp, status_code=status.HTTP_200_OK)
async def refresh(
    # === Response
    response: Response,
    # === Dependencies
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    # === Cookies
    rt: Annotated[Optional[str], Cookie()] = None,
):
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token missing. Please login again.",
        )

    async with handleDbOp(
        db, "Unable to retrieve information associated with the provided token."
    ):
        query = await db.execute(select(RefreshToken).where(RefreshToken.token == rt))
        dbToken = query.scalar_one_or_none()

    if not dbToken:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There isn't any entity associated with the provided token.",
        )

    if not dbToken.isActive:
        async with handleDbOp(
            db, "Unable to update information associated with the provided token."
        ):
            await db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.userAccountId == dbToken.userAccountId,
                    RefreshToken.isActive,
                )
                .values(
                    isActive=False,
                    rotatedAt=datetime.now(timezone.utc),
                )
                .execution_options(synchronize_session="fetch")
            )

            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session compromised or expired. Please sign in again.",
        )

    if dbToken.expiresAt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        async with handleDbOp(
            db, "Unable to update information associated with the provided token."
        ):
            dbToken.isActive = False
            await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired. Please sign in again.",
        )

    async with handleDbOp(db, "Internal server error verifying account credentials."):
        query = await db.execute(
            select(UserAccount).where(UserAccount.id == dbToken.userAccountId)
        )

        userAccount = query.scalar_one_or_none()

    if not userAccount or userAccount.isDisabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or does not exist anymore.",
        )

    dbToken.isActive = False
    dbToken.rotatedAt = datetime.now(timezone.utc)

    newAt = sec.generateAccessToken(
        userId=userAccount.id,
        role=userAccount.userRole,
        fed=userAccount.federationID,
    )

    tmpRt = sec.generateRandomToken()
    newRt = RefreshToken(
        token=tmpRt["token"],
        userAccountId=userAccount.id,
        expiresAt=tmpRt["exp"],
        isActive=True,
    )

    async with handleDbOp(db, "Internal server error during token rotation."):
        db.add(newRt)
        await db.commit()

    response.set_cookie(
        key="rt",
        value=newRt.token,
        max_age=sec.env.RT_EXP_MIN * 60,
        httponly=True,
        # secure=True,
        samesite="lax",
    )

    return TokenResp(at=newAt, tt="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    # Request Body
    userLogout: LogoutReq,
    # === Response
    response: Response,
    # === Dependencies
    db: Annotated[AsyncSession, Depends(dbHandler)],
    sec: Annotated[SecurityHandler, Depends(secHandler)],
    # at: Annotated[HTTPAuthorizationCredentials, Depends(tokenHandler)],
    # === Cookies
    rt: Annotated[Optional[str], Cookie()] = None,
):
    # if not rt or sec.verifyAccessToken(at.credentials):
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to logout, provide a valid token.",
        )

    async with handleDbOp(db, "Interval server error during logout processing."):
        res = await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token == rt,
                RefreshToken.userAccountId == userLogout.userId,
            )
            .values(
                isActive=False,
                rotatedAt=datetime.now(timezone.utc),
            )
        )

        await db.commit()

    if res.rowcount == 0:
        # TODO: Add Logging
        print("Zero Rows")
        pass

    response.set_cookie(
        key="rt",
        value="",
        max_age=0,
        httponly=True,
        samesite="lax",
    )
