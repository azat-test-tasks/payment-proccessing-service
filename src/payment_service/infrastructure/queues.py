from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

DLX = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)
NEW_QUEUE = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.failed",
    },
)
DLQ = RabbitQueue("payments.dlq", durable=True, routing_key="payments.failed")
