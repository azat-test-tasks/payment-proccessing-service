from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from payment_service.domain.enums import Currency, PaymentStatus


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Currency
    description: str = Field(min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: AnyHttpUrl


class PaymentAccepted(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentResponse(PaymentAccepted):
    model_config = ConfigDict(from_attributes=True)

    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    idempotency_key: str
    webhook_url: str
    processed_at: datetime | None
