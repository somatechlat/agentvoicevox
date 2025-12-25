# ==========================================================================
# AgentVoiceBox Backend Makefile
# ==========================================================================

.PHONY: help install install-dev format lint check test migrate \
        docker-up docker-down docker-logs docker-build docker-clean \
        shell dbshell worker

# Default target
help:
	@echo "AgentVoiceBox Backend Commands"
	@echo "=============================="
	@echo ""
	@echo "Development:"
	@echo "  install       Install production dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo "  format        Format code with Black and isort"
	@echo "  lint          Lint code with Ruff"
	@echo "  check         Run format check and lint"
	@echo "  test          Run pytest"
	@echo ""
	@echo "Django:"
	@echo "  migrate       Run database migrations"
	@echo "  shell         Open Django shell"
	@echo "  dbshell       Open database shell"
	@echo "  worker        Start Temporal worker"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up     Start all services"
	@echo "  docker-down   Stop all services"
	@echo "  docker-logs   Tail container logs"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-clean  Remove containers and volumes"

# ==========================================================================
# Development
# ==========================================================================

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black isort ruff pytest pytest-django pytest-asyncio hypothesis

format:
	black --line-length 100 .
	isort --profile black --line-length 100 .

lint:
	ruff check .

check:
	black --check --line-length 100 .
	isort --check-only --profile black --line-length 100 .
	ruff check .

test:
	pytest -v --tb=short

test-cov:
	pytest -v --cov=apps --cov-report=term-missing --cov-report=html

# ==========================================================================
# Django
# ==========================================================================

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell_plus

dbshell:
	python manage.py dbshell

collectstatic:
	python manage.py collectstatic --noinput

worker:
	python manage.py run_temporal_worker

createsuperuser:
	python manage.py createsuperuser

# ==========================================================================
# Docker
# ==========================================================================

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build

docker-clean:
	docker compose down -v --remove-orphans
	docker system prune -f

docker-restart:
	docker compose restart

docker-ps:
	docker compose ps

# Backend specific
docker-backend-logs:
	docker compose logs -f backend

docker-backend-shell:
	docker compose exec backend python manage.py shell

docker-backend-bash:
	docker compose exec backend /bin/bash

# Database
docker-db-shell:
	docker compose exec postgres psql -U agentvoicebox -d agentvoicebox

docker-db-backup:
	docker compose exec postgres pg_dump -U agentvoicebox agentvoicebox > backup_$$(date +%Y%m%d_%H%M%S).sql

# Temporal
docker-temporal-logs:
	docker compose logs -f temporal temporal-worker

# ==========================================================================
# Production
# ==========================================================================

prod-deploy:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

prod-migrate:
	docker compose exec backend python manage.py migrate --noinput

prod-collectstatic:
	docker compose exec backend python manage.py collectstatic --noinput
