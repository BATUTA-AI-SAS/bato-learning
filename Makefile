SHELL := /bin/bash

.PHONY: up down logs sh seed migrate revision build fmt test reset dev

# Bring everything up via Docker (preferred).
up:
	docker compose -f compose.yaml up -d --build

# Run locally without Docker (uv + uvicorn). Useful when Docker integration is off.
dev:
	mkdir -p data
	uv sync
	uv run alembic upgrade head
	uv run python -m scripts.seed
	uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8080

down:
	docker compose -f compose.yaml down

logs:
	docker compose -f compose.yaml logs -f app

sh:
	docker compose -f compose.yaml exec app bash

migrate:
	docker compose -f compose.yaml exec app uv run alembic upgrade head

revision:
	docker compose -f compose.yaml exec app uv run alembic revision --autogenerate -m "$(m)"

seed:
	docker compose -f compose.yaml exec app uv run python -m scripts.seed

reset:
	docker compose -f compose.yaml down -v
	rm -rf data
	mkdir -p data
	$(MAKE) up

fmt:
	uv run ruff check --fix app scripts

test:
	docker compose -f compose.yaml exec app uv run pytest -x
