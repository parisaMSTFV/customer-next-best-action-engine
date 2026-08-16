PYTHON ?= python

.PHONY: install run integration test lint sensitive check clean

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m next_best_action --project-root . --output-dir local-runs/latest

integration:
	$(PYTHON) -m next_best_action --project-root . --input-dir data/fixtures/upstream-v1 --output-dir artifacts/external-fixture

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

sensitive:
	$(PYTHON) scripts/check_sensitive.py

check: lint test integration sensitive

clean:
	rm -rf data/generated/*.csv artifacts .pytest_cache .ruff_cache
