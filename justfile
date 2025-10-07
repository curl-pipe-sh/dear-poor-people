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
    shellcheck -x $( { find . -type f -name '*.sh' -not -path './.git/*' ; grep -rlI --max-count=1 '^#!.*sh' . --exclude-dir=.git ; } | sort -u )

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

trim:
    git ls-files | xargs --verbose sed -r -i 's#[[:space:]]+$##'

# Run pre-commit hooks on all files
pre-commit:
    uv run pre-commit run --all-files

# Build Docker image
docker-build tag="poor-tools":
    @GIT_SHA=$(git rev-parse --short=8 HEAD 2>/dev/null || echo "unknown"); \
    docker build --build-arg GIT_COMMIT_SHA="$GIT_SHA" -t {{ tag }} .

# Run Docker container
docker-run tag="poor-tools" port="7667":
    docker run -p {{ port }}:7667 {{ tag }}

# Show project info
info:
    @echo "📦 poor-tools Web Installer"
    @echo "🐍 Python version: $(python --version)"
    @echo "📋 Available tools:"
    @find -maxdepth 1 -type f -name "poor*" -exec basename {} \; | sort

# Run comprehensive CI checks (what CI would run)
ci: install lint format-check typecheck test
    @echo "🎉 All CI checks passed!"
