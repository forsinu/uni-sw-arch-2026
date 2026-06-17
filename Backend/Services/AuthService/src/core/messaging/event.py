from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    FEDERATION_MEMBER_CREATED = "federation.member.created"
    FEDERATION_MEMBER_REMOVED = "federation.member.removed"
    FEDERATION_MEMBER_FEDERATION_CHANGED = "federation.member.federation.changed"


class DomainEvent(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    eventId: UUID = Field(alias="eventId")
    eventVersion: int = Field(alias="eventVersion")
    eventType: EventType = Field(alias="eventType")
    source: str
    occurredAt: datetime = Field(alias="occurredAt")


class FederationMemberCreatedData(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    federationId: str = Field(alias="federationId")
    firstName: str = Field(alias="firstName")
    lastName: str = Field(alias="lastName")
    changedBy: UUID | None = Field(default=None, alias="changedBy")


class FederationMemberRemovedData(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    federationId: str = Field(alias="federationId")
    changedBy: UUID | None = Field(default=None, alias="changedBy")


class FederationMemberFederationChangedData(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    oldFederationId: str | None = Field(default=None, alias="oldFederationId")
    newFederationId: str | None = Field(default=None, alias="newFederationId")
    changedBy: UUID | None = Field(default=None, alias="changedBy")


class FederationMemberCreatedEvent(DomainEvent):
    eventType: EventType = Field(
        default=EventType.FEDERATION_MEMBER_CREATED,
        alias="eventType",
    )

    data: FederationMemberCreatedData


class FederationMemberRemovedEvent(DomainEvent):
    eventType: EventType = Field(
        default=EventType.FEDERATION_MEMBER_REMOVED,
        alias="eventType",
    )

    data: FederationMemberRemovedData


class FederationMemberFederationChangedEvent(DomainEvent):
    eventType: EventType = Field(
        default=EventType.FEDERATION_MEMBER_FEDERATION_CHANGED,
        alias="eventType",
    )

    data: FederationMemberFederationChangedData


FederationEvent = (
    FederationMemberCreatedEvent
    | FederationMemberRemovedEvent
    | FederationMemberFederationChangedEvent
)
