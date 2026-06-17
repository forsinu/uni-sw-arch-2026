from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    FEDERATION_MEMBER_CREATED = "federation.member.created"
    FEDERATION_MEMBER_REMOVED = "federation.member.removed"
    FEDERATION_MEMBER_FEDERATION_CHANGED = "federation.member.federation.changed"


class DomainEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    eventId: UUID = Field(default_factory=uuid4, alias="eventId")
    eventVersion: int = Field(default=1, alias="eventVersion")
    eventType: EventType = Field(alias="eventType")
    source: str = "federation-service"
    occurredAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        alias="occurredAt",
    )


class FederationMemberCreatedData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # userAccountId: UUID = Field(alias="userAccountId")
    federationId: str = Field(alias="federationId")
    firstName: str = Field(alias="firstName")
    lastName: str = Field(alias="lastName")

    changedBy: UUID | None = Field(default=None, alias="changedBy")


class FederationMemberRemovedData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # userAccountId: UUID = Field(alias="userAccountId")
    federationId: str = Field(alias="federationId")

    changedBy: UUID | None = Field(default=None, alias="changedBy")


class FederationMemberFederationChangedData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # userAccountId: UUID = Field(alias="userAccountId")

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
