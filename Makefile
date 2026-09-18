UV := uv
PYTHON := $(UV) run python
COMPOSE := docker compose

.DEFAULT_GOAL := help
.PHONY: help install lock sync run worker migrate revision lint format format-check test check \
	build up down restart logs ps clean docker-test

help: ## Show all available commands.
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Create .venv and install runtime and development dependencies.
	$(UV) sync --all-groups

lock: ## Resolve dependencies and update uv.lock.
	$(UV) lock

sync: ## Synchronize .venv exactly from uv.lock.
	$(UV) sync --locked --all-groups

run: ## Start the API locally with hot reload.
	$(UV) run uvicorn payment_service.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Start the RabbitMQ payment consumer locally.
	$(UV) run python -m payment_service.worker

migrate: ## Apply all Alembic migrations to the configured database.
	$(UV) run alembic upgrade head

revision: ## Generate migration; use: make revision MSG='add field'.
	@test -n "$(MSG)" || (echo "MSG is required: make revision MSG='description'"; exit 1)
	$(UV) run alembic revision --autogenerate -m "$(MSG)"

lint: ## Run Ruff static checks.
	$(UV) run ruff check .

format: ## Format Python and TOML files with Ruff.
	$(UV) run ruff format .

format-check: ## Verify formatting without modifying files.
	$(UV) run ruff format --check .

test: ## Run the automated test suite.
	$(UV) run pytest -q

check: format-check lint test ## Run the complete local quality gate.

build: ## Build Docker images.
	$(COMPOSE) build

.env:
	@test -f .env || cp .env.example .env

up: .env ## Start PostgreSQL, RabbitMQ, API, and consumer in background.
	$(COMPOSE) up -d --build

down: ## Stop and remove Docker containers and network.
	$(COMPOSE) down

restart: ## Restart running Docker services.
	$(COMPOSE) restart

logs: ## Follow Docker service logs; use: make logs SERVICE=consumer.
	$(COMPOSE) logs -f $(SERVICE)

ps: ## Show Docker service state.
	$(COMPOSE) ps

clean: ## Stop stack and remove its named volumes.
	$(COMPOSE) down -v

docker-test: ## Run tests in the API image with development dependencies.
	$(COMPOSE) run --rm --no-deps api sh -c 'uv sync --all-groups && uv run pytest -q'
