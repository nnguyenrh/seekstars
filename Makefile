# StarSeek Makefile (Monorepo)
# Run 'make help' to see available targets.

.DEFAULT_GOAL := help

# ── Configuration ────────────────────────────────────────

VENV         := .venv
PYTHON       := $(VENV)/bin/python
PIP          := $(VENV)/bin/pip
PYTEST       := $(VENV)/bin/pytest
RUFF         := $(VENV)/bin/ruff
UVICORN      := $(VENV)/bin/uvicorn
CLI          := $(VENV)/bin/starseek
HOST         ?= 0.0.0.0
PORT         ?= 8000

# ── Guards ───────────────────────────────────────────────

.PHONY: _check-venv
_check-venv:
	@test -d $(VENV) || (echo "Error: Virtual environment not found. Run 'make reset-venv' first." && exit 1)

# ── Development ──────────────────────────────────────────

.PHONY: install
install: _check-venv  ## Install all packages in editable mode
	$(PIP) install -e "./starseek-core[dev]"
	$(PIP) install -e "./starseek-charts[dev]"
	$(PIP) install -e "./starseek-ui[dev]"

.PHONY: install-core
install-core: _check-venv  ## Install only starseek-core (lightweight, no rendering)
	$(PIP) install -e "./starseek-core[dev]"

# ── Running ──────────────────────────────────────────────

.PHONY: run
run: _check-venv  ## Start the API server (default: 0.0.0.0:8000)
	$(UVICORN) starseek.api.app:app --host $(HOST) --port $(PORT) --reload

.PHONY: chart
chart: _check-venv  ## Generate a chart via CLI. Usage: make chart ARGS="--date '...' --city '...'"
	$(CLI) chart $(ARGS)

# ── Testing ──────────────────────────────────────────────

.PHONY: test
test: _check-venv  ## Run all tests across all packages
	$(PYTEST) starseek-core/tests/ -v
	@if [ -d starseek-charts/tests ] && [ "$$(ls -A starseek-charts/tests/*.py 2>/dev/null)" ]; then \
		$(PYTEST) starseek-charts/tests/ -v; \
	fi
	@if [ -d starseek-ui/tests ] && [ "$$(ls -A starseek-ui/tests/*.py 2>/dev/null)" ]; then \
		$(PYTEST) starseek-ui/tests/ -v; \
	fi

.PHONY: test-core
test-core: _check-venv  ## Run starseek-core tests only
	$(PYTEST) starseek-core/tests/ -v

.PHONY: test-cov
test-cov: _check-venv  ## Run core tests with coverage report
	$(PYTEST) starseek-core/tests/ --cov=starseek --cov-report=term-missing --cov-report=html

# ── Code Quality ─────────────────────────────────────────

.PHONY: lint
lint: _check-venv  ## Run linter (ruff)
	$(RUFF) check starseek-core/starseek/ starseek-core/tests/

.PHONY: format
format: _check-venv  ## Auto-format code (ruff)
	$(RUFF) format starseek-core/starseek/ starseek-core/tests/

.PHONY: check
check: lint test  ## Run linter + all tests (pre-commit quality gate)

# ── Cleanup ──────────────────────────────────────────────

.PHONY: clean
clean:  ## Remove build artifacts, caches, and compiled files
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -rf *.egg-info dist build
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.egg-info' -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: reset-venv
reset-venv:  ## Destroy and recreate the virtualenv with all packages
	rm -rf $(VENV)
	python3.11 -m venv $(VENV)
	$(PIP) install -e "./starseek-core[dev]"

# ── Help ─────────────────────────────────────────────────

.PHONY: help
help:  ## Show this help message
	@echo "StarSeek - Astrological Birth Chart Generator (Monorepo)"
	@echo ""
	@echo "Quick start:  make reset-venv && make test"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
