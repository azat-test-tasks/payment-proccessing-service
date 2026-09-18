import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from payment_service.domain.enums import Currency, PaymentStatus


def enum_values(enum_class: type[Currency] | type[PaymentStatus]) -> list[str]:
    return [member.value for member in enum_class]


class Base(DeclarativeBase):
    pass


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", values_callable=enum_values), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=enum_values),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    webhook_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OutboxModel(Base):
    __tablename__ = "outbox"
    __table_args__ = (UniqueConstraint("event_type", "aggregate_id", name="uq_outbox_event_aggregate"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
