# Payment Processing Service

Асинхронный сервис обработки платежей на FastAPI. Он принимает платёж, надёжно фиксирует намерение обработать его в PostgreSQL, передаёт задачу через RabbitMQ и уведомляет клиента о результате webhook-вызовом.

## Установка
Склонируйте репозиторий и перейдите в него:

```bash
git clone https://github.com/azat-test-tasks/payment-processing-service.git
```

Создайте `.env` на основе `.env.example` и задайте свой `API_KEY`:

```bash
cp .env.example .env
```


## Запуск: Docker

```bash
make up
make ps
```

Показать логи:

```bash
make logs
make logs SERVICE=consumer
```

Остановить окружение:

```bash
make down
```

## Локальный запуск

```bash
make install
make sync
```

## Команды Makefile

```bash
make help
```

## Тестирование

```bash
make check
```


## Технологии

- Python 3.12+, FastAPI, Pydantic v2
- SQLAlchemy 2.0 async, Alembic, asyncpg, PostgreSQL 16
- FastStream, aio-pika, RabbitMQ 3.13
- httpx
- uv, Docker Compose, Ruff, pytest
