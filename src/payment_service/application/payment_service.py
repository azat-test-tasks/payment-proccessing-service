import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.api.schemas import PaymentCreate
from payment_service.domain.enums import PaymentStatus
from payment_service.infrastructure.models import OutboxModel, PaymentModel


class PaymentNotFoundError(Exception):
    pass


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, command: PaymentCreate, idempotency_key: str) -> PaymentModel:
        existing = await self._by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        payment = PaymentModel(
            amount=command.amount,
            currency=command.currency,
            description=command.description,
            metadata_=command.metadata,
            idempotency_key=idempotency_key,
            webhook_url=str(command.webhook_url),
        )
        self._session.add(payment)
        try:
            await self._session.flush()
            self._session.add(
                OutboxModel(
                    aggregate_id=payment.id,
                    event_type="payment.created",
                    payload={"event_id": str(uuid.uuid4()), "payment_id": str(payment.id)},
                )
            )
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            payment = await self._by_idempotency_key(idempotency_key)
            if payment is None:
                raise
        await self._session.refresh(payment)
        return payment

    async def get(self, payment_id: uuid.UUID) -> PaymentModel:
        payment = await self._session.get(PaymentModel, payment_id)
        if payment is None:
            raise PaymentNotFoundError
        return payment

    async def _by_idempotency_key(self, key: str) -> PaymentModel | None:
        result = await self._session.execute(select(PaymentModel).where(PaymentModel.idempotency_key == key))
        return result.scalar_one_or_none()

    async def set_result(self, payment_id: uuid.UUID, status: PaymentStatus) -> PaymentModel:
        payment = await self.get(payment_id)
        payment.status = status
        payment.processed_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(payment)
        return payment
