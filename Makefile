# ForgeAI developer commands. Run `make help` for the list.

.DEFAULT_GOAL := help
SHELL := /bin/bash

# ---- Environment ----
.PHONY: env
env: ## Create .env from .env.example if it does not exist
	@test -f .env || (cp .env.example .env && echo "Created .env from .env.example")
	@echo ".env is ready"

# ---- Docker stack ----
.PHONY: up
up: env ## Start all services (postgres, redis, qdrant, ollama, api)
	docker compose up -d --build

.PHONY: down
down: ## Stop all services
	docker compose down

.PHONY: restart
restart: down up ## Restart the whole stack

.PHONY: logs
logs: ## Tail logs for all services
	docker compose logs -f

.PHONY: ps
ps: ## Show running services
	docker compose ps

.PHONY: clean
clean: ## Stop services and remove volumes (DELETES ALL LOCAL DATA)
	docker compose down -v

# ---- AI models ----
.PHONY: pull-models
pull-models: ## Pull required Ollama models (large download, run once)
	bash scripts/pull-models.sh

# ---- Backend (host, via uv) ----
.PHONY: api-install
api-install: ## Install backend deps locally with uv
	cd apps/api && uv sync

.PHONY: api-dev
api-dev: ## Run the API locally with autoreload
	cd apps/api && PYTHONPATH="$(CURDIR)/apps/api:$(CURDIR)/packages" uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: api-fmt
api-fmt: ## Format & lint backend (black + ruff)
	cd apps/api && uv run black . && uv run ruff check --fix .

# ---- Frontend (host) ----
.PHONY: web-install
web-install: ## Install frontend deps
	cd apps/web && npm install

.PHONY: web-dev
web-dev: ## Run the Next.js dev server
	cd apps/web && npm run dev

# ---- Meta ----
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
