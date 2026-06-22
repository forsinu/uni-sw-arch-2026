import json
import logging
from typing import Callable

from src.db.errors import DbConflictError
from src.core.sec import SecurityHandler
from aio_pika import ExchangeType, IncomingMessage, connect_robust
from aio_pika.abc import (
    AbstractRobustChannel,
    AbstractRobustConnection,
    AbstractRobustExchange,
    AbstractRobustQueue,
)
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.environment import EnvHandler
from src.core.messaging.event import (
    DomainEvent,
    EventType,
    FederationEvent,
    FederationMemberCreatedEvent,
    FederationMemberFederationChangedEvent,
    FederationMemberRemovedEvent,
)
from src.db.repositories.user_account import UserAccountRepository


class RabbitMQHandler:
    def __init__(
        self,
        env: EnvHandler,
        sec: SecurityHandler,
        sessionFactory: async_sessionmaker[AsyncSession],
        userAccountRepositoryFactory: Callable[
            [AsyncSession],
            UserAccountRepository,
        ] = UserAccountRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self.env = env
        self.sec = sec

        self.rabbitmqUrl = env.RABBITMQ_URL

        self.sessionFactory = sessionFactory
        self.userAccountRepositoryFactory = userAccountRepositoryFactory

        self.logger = logger or logging.getLogger(__name__)

        self.exchangeName = env.FEDERATION_EVENTS_EXCHANGE
        self.queueName = env.AUTH_FEDERATION_QUEUE

        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._exchange: AbstractRobustExchange | None = None
        self._queue: AbstractRobustQueue | None = None
        self._consumerTag: str | None = None

    async def initialize(self) -> None:
        self._connection = await connect_robust(
            url=self.rabbitmqUrl,
        )

        self._channel = await self._connection.channel()

        await self._channel.set_qos(
            prefetch_count=10,
        )

        self._exchange = await self._channel.declare_exchange(
            self.exchangeName,
            ExchangeType.TOPIC,
            durable=True,
        )

        self._queue = await self._channel.declare_queue(
            self.queueName,
            durable=True,
        )

        await self._bindQueue()

        self._consumerTag = await self._queue.consume(
            self._handleMessage,
            no_ack=False,
        )

        self.logger.info(
            "RabbitMQ consumer connected: exchange=%s queue=%s host=%s port=%s",
            self.exchangeName,
            self.queueName,
            self.env.RABBITMQ_SERVICE_HOST,
            self.env.RABBITMQ_SERVICE_PORT,
        )

    async def close(self) -> None:
        if self._queue is not None and self._consumerTag is not None:
            await self._queue.cancel(self._consumerTag)

        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()

        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()

        self.logger.info("RabbitMQ consumer connection closed")

    async def _bindQueue(self) -> None:
        if self._queue is None or self._exchange is None:
            raise RuntimeError("RabbitMQHandler is not connected")

        routingKeys = (
            EventType.FEDERATION_MEMBER_CREATED.value,
            EventType.FEDERATION_MEMBER_REMOVED.value,
            EventType.FEDERATION_MEMBER_FEDERATION_CHANGED.value,
        )

        for routingKey in routingKeys:
            await self._queue.bind(
                self._exchange,
                routing_key=routingKey,
            )

            self.logger.info(
                "RabbitMQ queue bound: queue=%s routingKey=%s",
                self.queueName,
                routingKey,
            )

    async def _handleMessage(self, message: IncomingMessage) -> None:
        try:
            event = self._decodeEvent(message.body)

            await self._handleFederationEvent(event)

        except ValidationError as exc:
            self.logger.exception(
                "Invalid RabbitMQ event payload. messageId=%s error=%s",
                message.message_id,
                exc,
            )

            await message.reject(requeue=False)
            return

        except json.JSONDecodeError as exc:
            self.logger.exception(
                "Invalid RabbitMQ JSON payload. messageId=%s error=%s",
                message.message_id,
                exc,
            )

            await message.reject(requeue=False)
            return

        except Exception as exc:
            self.logger.exception(
                "RabbitMQ event handling failed. messageId=%s error=%s",
                message.message_id,
                exc,
            )

            await message.reject(requeue=True)
            return

        await message.ack()

    def _decodeEvent(self, body: bytes) -> FederationEvent:
        rawPayload = json.loads(body.decode("utf-8"))

        baseEvent = DomainEvent.model_validate(rawPayload)

        match baseEvent.eventType:
            case EventType.FEDERATION_MEMBER_CREATED:
                return FederationMemberCreatedEvent.model_validate(rawPayload)

            case EventType.FEDERATION_MEMBER_REMOVED:
                return FederationMemberRemovedEvent.model_validate(rawPayload)

            case EventType.FEDERATION_MEMBER_FEDERATION_CHANGED:
                return FederationMemberFederationChangedEvent.model_validate(rawPayload)

            case _:
                raise ValueError(f"Unsupported event type: {baseEvent.eventType}")

    async def _handleFederationEvent(
        self,
        event: FederationEvent,
    ) -> None:
        async with self.sessionFactory() as session:
            async with session.begin():
                userRepository = self.userAccountRepositoryFactory(session)

                match event:
                    case FederationMemberCreatedEvent():
                        await self._handleFederationMemberCreated(
                            event,
                            userRepository,
                        )

                    case FederationMemberRemovedEvent():
                        await self._handleFederationMemberRemoved(
                            event,
                            userRepository,
                        )

                    case FederationMemberFederationChangedEvent():
                        await self._handleFederationMemberFederationChanged(
                            event,
                            userRepository,
                        )

    def _normalizeUsernamePart(self, value: str) -> str:
        return (
            value.strip().lower().replace(" ", ".").replace("'", "").replace("-", ".")
        )

    def _buildFederationUsername(
        self,
        firstName: str,
        lastName: str,
        federationMemberId: str,
    ) -> str:
        first = self._normalizeUsernamePart(firstName)
        last = self._normalizeUsernamePart(lastName)

        # suffix = federationMemberId.replace("-", "")[:8]

        username = f"{first}.{last}"

        return username[:32]

    async def _handleFederationMemberCreated(
        self,
        event: FederationMemberCreatedEvent,
        userRepository: UserAccountRepository,
    ) -> None:
        username = self._buildFederationUsername(
            firstName=event.data.firstName,
            lastName=event.data.lastName,
            federationMemberId=event.data.federationId,
        )

        try:
            user = await userRepository.createUser(
                username=username,
                email=None,
                hashedPassword=self.sec.hashPassword(username),
                federationId=event.data.federationId,
            )

        except DbConflictError:
            self.logger.warning(
                "Federation-created user already exists or username conflict occurred: "
                "username=%s federationMemberId=%s federationId=%s eventId=%s",
                username,
                event.data.federationMemberId,
                event.data.federationId,
                event.eventId,
            )

            return

        self.logger.info(
            "Federation-created user account created: userAccountId=%s username=%s federationId=%s eventId=%s",
            user.id,
            user.username,
            event.data.federationId,
            event.eventId,
        )

    async def _handleFederationMemberRemoved(
        self,
        event: FederationMemberRemovedEvent,
        userRepository: UserAccountRepository,
    ) -> None:
        updated = await userRepository.setUserFedId(
            newFederationId=None,
        )

        if not updated:
            self.logger.warning(
                "User account not found while handling federation member removal: federationId=%s eventId=%s",
                event.data.federationId,
                event.eventId,
            )

            return

        self.logger.info(
            "User federation removed: previousFederationId=%s eventId=%s",
            event.data.federationId,
            event.eventId,
        )

    async def _handleFederationMemberFederationChanged(
        self,
        event: FederationMemberFederationChangedEvent,
        userRepository: UserAccountRepository,
    ) -> None:
        updated = await userRepository.setUserFedId(
            oldFederationId=event.data.oldFederationId,
            newFederationId=event.data.newFederationId,
        )

        if not updated:
            self.logger.warning(
                "User account not found while handling federation change: userAccountId=%s eventId=%s",
                event.data.oldFederationId,
                event.eventId,
            )

            return

        self.logger.info(
            "User federation changed: oldFederationId=%s newFederationId=%s eventId=%s",
            event.data.oldFederationId,
            event.data.newFederationId,
            event.eventId,
        )
