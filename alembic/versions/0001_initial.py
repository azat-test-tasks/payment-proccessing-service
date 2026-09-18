"""create payments and outbox tables

Revision ID: 0001
Revises:
Create Date: 2026-09-17
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    currency = sa.Enum("RUB", "USD", "EUR", name="currency")
    payment_status = sa.Enum("pending", "succeeded", "failed", name="payment_status")
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", currency, nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("webhook_url", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "outbox",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("aggregate_id", sa.Uuid(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.UniqueConstraint("event_type", "aggregate_id", name="uq_outbox_event_aggregate"),
    )


def downgrade() -> None:
    op.drop_table("outbox")
    op.drop_table("payments")
    sa.Enum(name="payment_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="currency").drop(op.get_bind(), checkfirst=True)
