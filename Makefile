.PHONY: install dev test lint format typecheck run docker

install:
	pip install .

dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src/sorteo_bot

run:
	python -m sorteo_bot

docker:
	docker build -t sorteo-bot .
