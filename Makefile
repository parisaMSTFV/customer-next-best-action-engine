PYTHON ?= python

.PHONY: install run test lint sensitive check clean

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m next_best_action --project-root .

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

sensitive:
	$(PYTHON) scripts/check_sensitive.py

check: lint test sensitive

clean:
	rm -rf data/generated/*.csv .pytest_cache .ruff_cache
