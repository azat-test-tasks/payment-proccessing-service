import asyncio

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from payment_service.application.processor import PaymentCreatedEvent, PaymentProcessor
from payment_service.core.config import get_settings
from payment_service.infrastructure.queues import DLQ, DLX, NEW_QUEUE

broker = RabbitBroker(get_settings().rabbitmq_url)
app = FastStream(broker)


async def declare_topology() -> None:
    exchange = await broker.declare_exchange(DLX)
    queue = await broker.declare_queue(DLQ)
    await queue.bind(exchange, routing_key=DLQ.routing_key)
    await broker.declare_queue(NEW_QUEUE)


@app.after_startup
async def setup_topology() -> None:
    await declare_topology()


@broker.subscriber(NEW_QUEUE)
async def handle_payment(message: dict[str, str]) -> None:
    event = PaymentCreatedEvent.from_message(message)
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            await PaymentProcessor().process(event)
            return
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(2**attempt)
    assert last_error is not None
    raise last_error


async def run_with_retry(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    for attempt in range(max_attempts):
        try:
            await app.run()
            return
        except Exception:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(delay_seconds)


if __name__ == "__main__":
    asyncio.run(run_with_retry())
