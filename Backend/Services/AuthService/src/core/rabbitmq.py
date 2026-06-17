import aio_pika


class RabbitMQHandler:
    def __init__(self, rabbitmqUrl: str) -> None:
        self.rabbitmqUrl = rabbitmqUrl
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None

    async def initialize(self) -> None:
        self.connection = await aio_pika.connect_robust(self.rabbitmqUrl)
        self.channel = await self.connection.channel()

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()

    async def publish(
        self,
        exchangeName: str,
        routingKey: str,
        body: bytes,
    ) -> None:
        if self.channel is None:
            raise RuntimeError("RabbitMQHandler has not been initialized")

        exchange = await self.channel.declare_exchange(
            exchangeName,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        await exchange.publish(
            aio_pika.Message(
                body=body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routingKey,
        )
