.PHONY: help install test lint format clean dev run examples

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@egrep '^(.+)\s*:.*##\s*(.+)' $(MAKEFILE_LIST) | column -t -c 2 -s ':#'

install: ## Install dependencies
	uv sync

dev: ## Install with dev dependencies
	uv sync --group dev

test: ## Run tests
	uv run pytest tests/ -v

lint: ## Run linting
	uv run ruff check src/ tests/ examples/
	uv run mypy src/

format: ## Format code
	uv run ruff format src/ tests/ examples/
	uv run isort src/ tests/ examples/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run: ## Run the MCP server
	uv run python -m youtube_api_server.server

examples: ## Run all examples
	@echo "Running API setup validation..."
	uv run python examples/api_setup_guide.py
	@echo "\nRunning basic usage examples..."
	uv run python examples/basic_usage.py
	@echo "\nRunning comparison demo..."
	uv run python examples/comparison_demo.py

validate: ## Validate the installation and API setup
	uv run python examples/api_setup_guide.py

build: ## Build the package
	uv build

release: test lint ## Prepare for release
	@echo "All checks passed! Ready for release."