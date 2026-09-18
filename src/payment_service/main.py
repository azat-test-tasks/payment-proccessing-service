import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from payment_service.api.routes import router
from payment_service.infrastructure.outbox import OutboxPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    publisher = OutboxPublisher()
    task = asyncio.create_task(publisher.run())
    try:
        yield
    finally:
        task.cancel()
        await publisher.close()


app = FastAPI(title="Payment Processing Service", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
