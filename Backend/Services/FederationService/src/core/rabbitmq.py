import json
import logging

from aio_pika import DeliveryMode, ExchangeType, Message, connect_robust
from aio_pika.abc import (
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractRobustExchange,
)

from src.core.environment import EnvHandler
from src.core.messaging.event import (
    DomainEvent,
    FederationMemberCreatedData,
    FederationMemberCreatedEvent,
    FederationMemberFederationChangedData,
    FederationMemberFederationChangedEvent,
    FederationMemberRemovedData,
    FederationMemberRemovedEvent,
)


class RabbitMQHandler:
    def __init__(
        self,
        env: EnvHandler,
        logger: logging.Logger | None = None,
    ) -> None:
        self.env = env

        self.rabbitmqUrl = env.RABBITMQ_URL
        self.exchangeName = env.FEDERATION_EVENTS_EXCHANGE

        self.logger = logger or logging.getLogger(__name__)

        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._exchange: AbstractRobustExchange | None = None

    async def initialize(self) -> None:
        self._connection = await connect_robust(
            url=self.rabbitmqUrl,
        )

        self._channel = await self._connection.channel(
            publisher_confirms=True,
        )

        self._exchange = await self._channel.declare_exchange(
            self.exchangeName,
            ExchangeType.TOPIC,
            durable=True,
        )

        self.logger.info(
            "RabbitMQ connected: exchange=%s host=%s port=%s",
            self.exchangeName,
            self.env.RABBITMQ_SERVICE_HOST,
            self.env.RABBITMQ_SERVICE_PORT,
        )

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()

        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()

        self.logger.info("RabbitMQ connection closed")

    def _requireExchange(self) -> AbstractRobustExchange:
        if self._exchange is None:
            raise RuntimeError("RabbitMQHandler is not connected")

        return self._exchange

    async def publishEvent(self, event: DomainEvent) -> None:
        exchange = self._requireExchange()

        routingKey = event.eventType.value

        body = json.dumps(
            event.model_dump(
                mode="json",
                by_alias=True,
            ),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        message = Message(
            body=body,
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=str(event.eventId),
            type=routingKey,
            headers={
                "eventType": routingKey,
                "eventVersion": event.eventVersion,
                "source": event.source,
            },
        )

        await exchange.publish(
            message,
            routing_key=routingKey,
            mandatory=True,
        )

        self.logger.info(
            "Published RabbitMQ event: type=%s id=%s",
            routingKey,
            event.eventId,
        )

    async def publishFederationMemberCreated(
        self,
        data: FederationMemberCreatedData,
    ) -> None:
        event = FederationMemberCreatedEvent(data=data)

        await self.publishEvent(event)

    async def publishFederationMemberRemoved(
        self,
        data: FederationMemberRemovedData,
    ) -> None:
        event = FederationMemberRemovedEvent(data=data)

        await self.publishEvent(event)

    async def publishFederationMemberFederationChanged(
        self,
        data: FederationMemberFederationChangedData,
    ) -> None:
        event = FederationMemberFederationChangedEvent(data=data)

        await self.publishEvent(event)
