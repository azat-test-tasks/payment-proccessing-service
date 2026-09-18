from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from payment_service.api.dependencies import require_api_key, session_dependency
from payment_service.api.schemas import PaymentAccepted, PaymentCreate, PaymentResponse
from payment_service.application.payment_service import (
    PaymentNotFoundError,
    PaymentService,
)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"], dependencies=[Depends(require_api_key)])


def to_response(payment: object) -> PaymentResponse:
    return PaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata_,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        processed_at=payment.processed_at,
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=PaymentAccepted)
async def create_payment(
    body: PaymentCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(session_dependency),
) -> PaymentAccepted:
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key is required")
    payment = await PaymentService(session).create(body, idempotency_key)
    response.headers["Location"] = f"/api/v1/payments/{payment.id}"
    return PaymentAccepted(payment_id=payment.id, status=payment.status, created_at=payment.created_at)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    session: AsyncSession = Depends(session_dependency),
) -> PaymentResponse:
    try:
        payment = await PaymentService(session).get(payment_id)
    except PaymentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found") from None
    return to_response(payment)
