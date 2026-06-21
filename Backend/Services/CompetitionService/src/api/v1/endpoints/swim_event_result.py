from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    AccessContext,
    adminOrRefereeAccessHandler,
    authenticatedAccessHandler,
    dbManagerHandler,
    dbSessionHandler,
    swimEventRepositoryHandler,
    swimEventResultRepositoryHandler,
)
from src.db.errors import DbConflictError
from src.db.repositories import SwimEventRepository, SwimEventResultRepository
from src.db.session import DatabaseHandler
from src.schemas.common import MessageResp
from src.schemas.swim_event_result import (
    PaginatedSwimEventResultResp,
    SwimEventResultResp,
    SwimEventResultUpsertReq,
)


router = APIRouter(
    tags=["Swim Event Results"],
)


@router.get(
    "/events/{eventId}/results",
    response_model=PaginatedSwimEventResultResp,
    status_code=status.HTTP_200_OK,
    operation_id="listSwimEventResults",
)
async def listSwimEventResults(
    eventId: uuid.UUID,
    # access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    resultRepository: Annotated[
        SwimEventResultRepository,
        Depends(swimEventResultRepositoryHandler),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    totalRecords, results = await resultRepository.listResultsByEventId(
        swimEventId=eventId,
        limit=limit,
        offset=offset,
    )

    return PaginatedSwimEventResultResp.model_validate(
        {
            "metadata": {
                "totalRecords": totalRecords,
                "limit": limit,
                "offset": offset,
                "hasMore": (offset + limit) < totalRecords,
            },
            "results": results,
        }
    )


@router.put(
    "/events/{eventId}/results",
    response_model=SwimEventResultResp,
    status_code=status.HTTP_200_OK,
    operation_id="upsertSwimEventResult",
)
async def upsertSwimEventResult(
    eventId: uuid.UUID,
    payload: SwimEventResultUpsertReq,
    access: Annotated[AccessContext, Depends(adminOrRefereeAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    eventRepository: Annotated[
        SwimEventRepository,
        Depends(swimEventRepositoryHandler),
    ],
    resultRepository: Annotated[
        SwimEventResultRepository,
        Depends(swimEventResultRepositoryHandler),
    ],
):
    try:
        async with database.transaction(session):
            event = await eventRepository.getEventById(eventId)

            if event is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Swim event not found.",
                )

            result = await resultRepository.upsertResult(
                swimEventId=eventId,
                federationId=payload.federationId,
                status=payload.status,
                finalTimeMs=payload.finalTimeMs,
                splitTimesMs=payload.splitTimesMs,
                disqualificationReason=payload.disqualificationReason,
            )

    except DbConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A conflicting result already exists for this athlete and event.",
        ) from exc

    return result


@router.get(
    "/results/{resultId}",
    response_model=SwimEventResultResp,
    status_code=status.HTTP_200_OK,
    operation_id="getSwimEventResult",
)
async def getSwimEventResult(
    resultId: uuid.UUID,
    # access: Annotated[AccessContext, Depends(authenticatedAccessHandler)],
    resultRepository: Annotated[
        SwimEventResultRepository,
        Depends(swimEventResultRepositoryHandler),
    ],
):
    result = await resultRepository.getResultById(resultId)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swim event result not found.",
        )

    return result


@router.delete(
    "/results/{resultId}",
    response_model=MessageResp,
    status_code=status.HTTP_200_OK,
    operation_id="deleteSwimEventResult",
)
async def deleteSwimEventResult(
    resultId: uuid.UUID,
    access: Annotated[AccessContext, Depends(adminOrRefereeAccessHandler)],
    database: Annotated[DatabaseHandler, Depends(dbManagerHandler)],
    session: Annotated[AsyncSession, Depends(dbSessionHandler)],
    resultRepository: Annotated[
        SwimEventResultRepository,
        Depends(swimEventResultRepositoryHandler),
    ],
):
    async with database.transaction(session):
        result = await resultRepository.getResultById(resultId)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swim event result not found.",
            )

        await resultRepository.deleteResult(result)

    return {"msg": "Swim event result deleted successfully."}
