import asyncio
from datetime import UTC, datetime

from faststream.rabbit import RabbitBroker
from sqlalchemy import select

from payment_service.core.config import get_settings
from payment_service.infrastructure.database import SessionFactory
from payment_service.infrastructure.models import OutboxModel
from payment_service.infrastructure.queues import DLQ, DLX, NEW_QUEUE


class OutboxPublisher:
    def __init__(self, broker: RabbitBroker | None = None) -> None:
        self._broker = broker or RabbitBroker(get_settings().rabbitmq_url)
        self._owns_broker = broker is None
        self._stopped = False
        self._topology_ready = False

    async def _ensure_topology(self) -> None:
        if self._topology_ready:
            return
        exchange = await self._broker.declare_exchange(DLX)
        queue = await self._broker.declare_queue(DLQ)
        await queue.bind(exchange, routing_key=DLQ.routing_key)
        await self._broker.declare_queue(NEW_QUEUE)
        self._topology_ready = True

    async def run(self) -> None:
        if self._owns_broker:
            await self._broker.connect()
        await self._ensure_topology()
        while not self._stopped:
            await self.publish_pending()
            await asyncio.sleep(get_settings().outbox_poll_interval_seconds)

    async def publish_pending(self) -> int:
        published = 0
        async with SessionFactory() as session:
            rows = await session.scalars(
                select(OutboxModel)
                .where(OutboxModel.published_at.is_(None))
                .order_by(OutboxModel.created_at)
                .with_for_update(skip_locked=True)
                .limit(100)
            )
            for event in rows:
                try:
                    await self._ensure_topology()
                    await self._broker.publish(event.payload, queue=NEW_QUEUE.name)
                except Exception as exc:
                    event.attempts += 1
                    event.last_error = str(exc)[:1000]
                else:
                    event.published_at = datetime.now(UTC)
                    event.last_error = None
                    published += 1
            await session.commit()
        return published

    async def close(self) -> None:
        self._stopped = True
        if self._owns_broker:
            await self._broker.close()
