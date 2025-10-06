# AGENTS.md

## Project Guidelines for AI Agents

This document provides guidelines for AI agents working on the poor-tools web installer project.

### Code Style

- **Python**: Follow PEP 8, use type hints, prefer explicit over implicit
- **Line length**: 88 characters (Black/Ruff default)
- **Imports**: Use `isort` style, group standard library, third-party, and local imports
- **Quotes**: Use double quotes for strings
- **Formatting**: Use `ruff format` (Black-compatible)
- **Whitespace**: Always trim trailing whitespace from all files

### Code Quality

- **Linting**: Use `ruff` for linting and formatting
- **Type checking**: Use `mypy` with strict settings
- **Testing**: Use `pytest` for all tests, aim for good coverage
- **Dependencies**: Manage with `uv`, pin versions in pyproject.toml
- **Docker**: Use `hadolint` for Dockerfile linting

### File Organization

```
.
├── main.py              # FastAPI application
├── lib/                 # Reusable shell functions
│   ├── echo.sh         # Echo utilities
│   └── utils.sh        # Common utilities
├── templates/           # Template files for dynamic generation
│   └── tool-installer.sh # Tool-specific installer template
├── tests/               # Test files
│   └── test_main.py    # Main test suite
├── pyproject.toml      # Project config
├── Dockerfile          # Container build
├── flake.nix           # Nix development/deployment
└── .github/workflows/  # CI/CD
```

### Development Workflow

1. **Setup**: Use `uv sync --all-extras --dev` to install dependencies
2. **Development**: Use the Nix dev shell or Python virtual environment
3. **Testing**: Run `uv run pytest tests/ -v` before committing
4. **Linting**: Run `uv run ruff check .` and `uv run ruff format .`
5. **Import sorting**: Run `uv run ruff check --select I .` to check import order
6. **Type checking**: Run `uv run mypy main.py`
7. **Docker linting**: Run `hadolint Dockerfile` for Docker best practices
8. **Pre-commit**: Use Nix dev shell for automatic native pre-commit hook setup
9. **CI**: All checks run independently - workflow fails only if any check fails

### API Design

- **Endpoints**: RESTful, clear naming
- **Responses**: Use appropriate HTTP status codes
- **Content-Type**: `text/plain; charset=utf-8` for scripts
- **Error handling**: Return meaningful error messages
- **Parameters**: Use query parameters for options (e.g., `?no_templating=1`)

### Shell Script Guidelines

- **Templating**: Support `# INCLUDE_FILE: path/to/file.sh` directives
- **Library functions**: Place reusable functions in `lib/`
- **Style**: Follow existing poor-tools style (POSIX shell where possible)
- **Comments**: Use meaningful comments for complex logic

### Testing

- **Unit tests**: Test all endpoints and core functionality
- **Integration tests**: Test templating system end-to-end
- **Mocking**: Mock file system operations when needed
- **Coverage**: Aim for high test coverage, especially for core logic

### Docker & Deployment

- **Base image**: Use official Python slim images
- **Security**: Run as non-root user, minimal permissions
- **Health checks**: Include proper health check endpoints
- **Environment**: Support configuration via environment variables
- **Logs**: Use structured logging, avoid sensitive data in logs

### Nix Integration

- **Flake**: Use flakes for reproducible builds
- **Dev shell**: Include all development dependencies
- **NixOS module**: Provide systemd service configuration
- **Security**: Use proper systemd security features

### Git & CI

- **Branches**: Use feature branches, merge to main
- **Commits**: Write clear, descriptive commit messages
- **CI**: All tests must pass, linting must be clean, hadolint must pass
- **Docker**: Automatically build and push container images
- **Releases**: Use semantic versioning for tags

### Security Considerations

- **Input validation**: Validate all user inputs
- **Path traversal**: Prevent directory traversal attacks
- **File access**: Only serve intended files
- **Headers**: Set appropriate security headers
- **Secrets**: Never commit secrets, use environment variables

### Performance

- **Caching**: Cache file contents when appropriate
- **Async**: Use async/await for I/O operations
- **Memory**: Be mindful of memory usage for large files
- **Concurrency**: Design for multiple concurrent requests

### Error Handling

- **Graceful degradation**: Handle missing files gracefully
- **Logging**: Log errors appropriately
- **User feedback**: Provide helpful error messages
- **Recovery**: Implement retry logic where appropriate

### Documentation

- **Code comments**: Document complex algorithms and business logic
- **API docs**: Use FastAPI's automatic OpenAPI documentation
- **README**: Keep installation instructions concise
- **Examples**: Provide usage examples
