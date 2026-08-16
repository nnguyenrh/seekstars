# StarSeek Makefile
# Run 'make help' to see available targets.

.DEFAULT_GOAL := help

# ── Configuration ────────────────────────────────────────

VENV         := .venv
PYTHON       := $(VENV)/bin/python
PIP          := $(VENV)/bin/pip
PYTEST       := $(VENV)/bin/pytest
RUFF         := $(VENV)/bin/ruff
UVICORN      := $(VENV)/bin/uvicorn
CLI          := $(PYTHON) -m starseek
HOST         ?= 0.0.0.0
PORT         ?= 8000
DB_PATH      ?= starseek.db

# ── Guards ───────────────────────────────────────────────

.PHONY: _check-venv
_check-venv:
	@test -d $(VENV) || (echo "Error: Virtual environment not found. Run ./setup.sh first." && exit 1)

# ── Development ──────────────────────────────────────────

.PHONY: install
install: _check-venv  ## Install/update production dependencies
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: _check-venv  ## Install/update dev + production dependencies
	$(PIP) install -r requirements.txt -r requirements-dev.txt

.PHONY: update
update: _check-venv  ## Update all dependencies to latest compatible versions
	$(PIP) install --upgrade -r requirements.txt -r requirements-dev.txt

# ── Running ──────────────────────────────────────────────

.PHONY: run
run: _check-venv  ## Start the API server (default: 0.0.0.0:8000)
	$(UVICORN) starseek.api.app:app --host $(HOST) --port $(PORT) --reload

.PHONY: chart
chart: _check-venv  ## Generate a chart via CLI. Usage: make chart ARGS="--datetime '...' --city '...'"
	$(CLI) chart $(ARGS)

# ── Testing ──────────────────────────────────────────────

.PHONY: test
test: _check-venv  ## Run all tests
	$(PYTEST) tests/ -v

.PHONY: test-unit
test-unit: _check-venv  ## Run unit tests only (fast)
	$(PYTEST) tests/ -v -m "not integration"

.PHONY: test-cov
test-cov: _check-venv  ## Run tests with coverage report
	$(PYTEST) tests/ --cov=starseek --cov-report=term-missing --cov-report=html

# ── Code Quality ─────────────────────────────────────────

.PHONY: lint
lint: _check-venv  ## Run linter (ruff)
	$(RUFF) check starseek/ tests/

.PHONY: format
format: _check-venv  ## Auto-format code (ruff)
	$(RUFF) format starseek/ tests/

.PHONY: check
check: lint test  ## Run linter + all tests (pre-commit quality gate)

# ── Cleanup ──────────────────────────────────────────────

.PHONY: clean
clean:  ## Remove build artifacts, caches, and compiled files
	rm -rf __pycache__ starseek/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -rf *.egg-info dist build
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: reset-venv
reset-venv:  ## Destroy and recreate the virtualenv with all dependencies
	rm -rf $(VENV)
	python3.11 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

# ── Help ─────────────────────────────────────────────────

.PHONY: help
help:  ## Show this help message
	@echo "StarSeek - Birth Chart Generator"
	@echo ""
	@echo "First-time setup:  ./setup.sh"
	@echo "                   ./setup.sh --dev  (include dev dependencies)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
