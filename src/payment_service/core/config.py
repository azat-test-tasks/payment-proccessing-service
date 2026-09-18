from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://payments:payments@localhost:5432/payments"
    rabbitmq_url: str = "amqp://payments:payments@localhost:5672/"
    api_key: str = "JHKAE5hTa9RYD5mQYZyTRxOYGyQS4CXV"
    outbox_poll_interval_seconds: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
