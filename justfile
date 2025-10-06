# Justfile for poor-tools development

# Default recipe to display available commands
default:
    @just --list

# Run all tests
test:
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    uv run pytest tests/ -v --cov=poor_installer_web --cov-report=term-missing

# Run linting checks
lint:
    uv run ruff check .

# Run linting with auto-fix
lint-fix:
    uv run ruff check --fix .

# Format code
format:
    uv run ruff format .

# Check formatting without making changes
format-check:
    uv run ruff format --check .

# Run type checking
typecheck:
    uv run mypy poor_installer_web/app.py

# Run all quality checks (lint, format, typecheck)
check: lint format-check typecheck
    @echo "✅ All quality checks passed!"

# Install dependencies
install:
    uv sync --all-extras --dev

# Run the development server
run host="127.0.0.1" port="7667":
    uv run python -m poor_installer_web.app --bind-host {{ host }} --bind-port {{ port }}

# Run the server with hot reload (using uvicorn directly)
dev host="127.0.0.1" port="7667":
    uv run uvicorn poor_installer_web.app:app --host {{ host }} --port {{ port }} --reload

# Clean up cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".mypy_cache" -exec rm -rf {} +
    find . -type d -name ".ruff_cache" -exec rm -rf {} +

# Run pre-commit hooks on all files
pre-commit:
    uv run pre-commit run --all-files

# Build Docker image
docker-build tag="poor-tools":
    docker build -t {{ tag }} .

# Run Docker container
docker-run tag="poor-tools" port="7667":
    docker run -p {{ port }}:7667 {{ tag }}

# Show project info
info:
    @echo "📦 poor-tools Web Installer"
    @echo "🐍 Python version: $(python --version)"
    @echo "📋 Available tools:"
    @ls -1 poor* | head -10

# Run comprehensive CI checks (what CI would run)
ci: install lint format-check typecheck test
    @echo "🎉 All CI checks passed!"