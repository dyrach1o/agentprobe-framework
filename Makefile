.PHONY: install dev test test-unit test-integration test-fast lint format type-check check docs docs-serve clean

install:                ## Install production dependencies
	pip install -e .

dev:                    ## Install with dev dependencies
	pip install -e ".[dev,test,docs]"

test:                   ## Run all tests
	pytest tests/

test-unit:              ## Run unit tests only
	pytest tests/unit/

test-integration:       ## Run integration tests only
	pytest tests/integration/ -m integration

test-fast:              ## Run tests excluding slow and API tests
	pytest tests/ -m "not slow and not api"

lint:                   ## Run linter
	ruff check src/ tests/

format:                 ## Format code
	ruff format src/ tests/

type-check:             ## Run type checker
	mypy src/agentprobe/

check:                  ## Run all checks (lint + type + test)
	ruff check src/ tests/
	mypy src/agentprobe/
	pytest tests/unit/

docs:                   ## Build documentation
	mkdocs build

docs-serve:             ## Serve documentation locally
	mkdocs serve

clean:                  ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
