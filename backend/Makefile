.PHONY: install lint format typecheck test check
COV_MIN ?= 90

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

typecheck:
	mypy src tests

test:
	pytest --cov=windfc --cov-report=term-missing --cov-fail-under=$(COV_MIN)

check: lint typecheck test

run:
	uvicorn windfc.api.main:app --reload
