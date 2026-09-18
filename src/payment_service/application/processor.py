import asyncio
import random
from dataclasses import dataclass
from uuid import UUID

import httpx

from payment_service.application.payment_service import PaymentService
from payment_service.domain.enums import PaymentStatus
from payment_service.infrastructure.database import SessionFactory


@dataclass(frozen=True)
class PaymentCreatedEvent:
    event_id: UUID
    payment_id: UUID

    @classmethod
    def from_message(cls, data: dict[str, str]) -> "PaymentCreatedEvent":
        return cls(event_id=UUID(data["event_id"]), payment_id=UUID(data["payment_id"]))


class PaymentProcessor:
    def __init__(self, success_probability: float = 0.9) -> None:
        self._success_probability = success_probability

    async def process(self, event: PaymentCreatedEvent) -> None:
        async with SessionFactory() as session:
            service = PaymentService(session)
            payment = await service.get(event.payment_id)
            if payment.status is not PaymentStatus.PENDING:
                await self._notify(payment)
                return
            await asyncio.sleep(random.uniform(2, 5))
            result = PaymentStatus.SUCCEEDED if random.random() < self._success_probability else PaymentStatus.FAILED
            payment = await service.set_result(event.payment_id, result)
            await self._notify(payment)

    async def _notify(self, payment: object) -> None:
        payload = {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "processed_at": payment.processed_at.isoformat(),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(payment.webhook_url, json=payload)
            response.raise_for_status()
