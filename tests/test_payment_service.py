from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from payment_service.api.schemas import PaymentCreate
from payment_service.application.payment_service import PaymentNotFoundError, PaymentService
from payment_service.domain.enums import Currency, PaymentStatus
from payment_service.infrastructure.models import Base, OutboxModel


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def command() -> PaymentCreate:
    return PaymentCreate(
        amount=Decimal("120.50"),
        currency=Currency.RUB,
        description="Order #42",
        metadata={"order_id": 42},
        webhook_url="https://example.test/webhooks/payment",
    )


async def test_create_payment_writes_payment_and_outbox(session_factory) -> None:
    async with session_factory() as session:
        payment = await PaymentService(session).create(command(), "request-42")
        outbox = (await session.scalars(select(OutboxModel))).one()

    assert payment.status is PaymentStatus.PENDING
    assert outbox.aggregate_id == payment.id
    assert outbox.payload["payment_id"] == str(payment.id)


async def test_payment_status_is_persisted_as_its_lowercase_domain_value(session_factory) -> None:
    async with session_factory() as session:
        await PaymentService(session).create(command(), "status-value")
        stored_status = await session.scalar(text("SELECT status FROM payments"))

    assert stored_status == PaymentStatus.PENDING.value


async def test_idempotency_returns_original_payment_and_one_event(session_factory) -> None:
    async with session_factory() as session:
        service = PaymentService(session)
        first = await service.create(command(), "same-key")
        second = await service.create(command(), "same-key")
        events = (await session.scalars(select(OutboxModel))).all()

    assert second.id == first.id
    assert len(events) == 1


async def test_get_missing_payment_raises_domain_error(session_factory) -> None:
    async with session_factory() as session:
        with pytest.raises(PaymentNotFoundError):
            await PaymentService(session).get(uuid4())
