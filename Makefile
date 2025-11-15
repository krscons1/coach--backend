.PHONY: help install dev test lint migrate seed train clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev         - Start development server"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make migrate     - Run database migrations"
	@echo "  make seed        - Seed database with sample data"
	@echo "  make train       - Train ML model"
	@echo "  make clean       - Clean temporary files"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest --cov=app --cov-report=term-missing

lint:
	black --check app/
	ruff check app/
	mypy app/

migrate:
	alembic upgrade head

seed:
	python -m app.db.seed

train:
	python -m app.ml.train

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

