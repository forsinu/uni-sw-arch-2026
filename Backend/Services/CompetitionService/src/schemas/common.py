from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class PaginationMetadata(BaseSchema):
    totalRecords: int
    limit: int
    offset: int
    hasMore: bool


class PaginatedResp(BaseSchema, Generic[T]):
    metadata: PaginationMetadata
    results: Sequence[T]


class MessageResp(BaseSchema):
    msg: str
