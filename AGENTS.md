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
- **Shell scripts**: Use `shellcheck` for shell script linting
  - All `poor*` scripts in this repository are POSIX `sh`

### File Organization

```
.
├── poor_installer_web.py  # FastAPI application
├── lib/                   # Reusable shell functions
│   ├── echo.sh           # Echo utilities
│   └── utils.sh          # Common utilities
├── templates/             # Template files for dynamic generation
│   └── tool-installer.sh # Tool-specific installer template
├── tests/                 # Test files
│   └── test_main.py      # Test suite
├── pyproject.toml        # Project config
├── Dockerfile            # Container build
├── flake.nix             # Nix development/deployment
└── .github/workflows/    # CI/CD
```

### Development Workflow

1. **Setup**: Use `uv sync --all-extras --dev` to install dependencies
2. **Development**: Use the Nix dev shell or Python virtual environment
3. **Testing**: Run `uv run pytest tests/ -v` before committing
4. **Linting**: Run `uv run ruff check .` and `uv run ruff format .`
5. **Import sorting**: Run `uv run ruff check --select I .` to check import order
6. **Type checking**: Run `uv run mypy poor_installer_web.py`
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
- **Library usage**: Source shared helpers with `. lib/<file>.sh # <TEMPLATE>` so the
  web installer can inline them automatically
- **Style**: Follow existing poor-tools style (POSIX shell where possible)
- **Comments**: Use meaningful comments for complex logic
- **Variable naming**: Use UPPERCASE for global variables, lowercase for local variables
- **Control flow style**: Prefer explicit if/then/fi blocks over compact one-liners:
  ```bash
  # Good:
  if [ $# -lt 2 ]
  then
    echo_error "insufficient arguments"
    return 2
  fi

  # Avoid:
  [ $# -ge 2 ] || { echo_error "insufficient arguments"; return 2; }
  ```
- **Script structure**: Always organize scripts with these patterns:
  ```bash
  #!/usr/bin/env sh
  # description: Brief description
  # icon: mdi:icon-name

  set -eu

  # Global variables (UPPERCASE)
  SCRIPT_NAME="scriptname"

  # Source libraries
  . lib/echo.sh # <TEMPLATE>

  # Define usage function
  usage() {
    cat <<USAGE >&2
  Usage: ${SCRIPT_NAME} [options] arguments
  Description of what the script does.

  Options:
    --debug    Enable debug output
    -h, --help Show this help
  USAGE
  }

  # Helper functions (if needed)
  helper_function() {
    # Implementation
  }

  # Main function contains the primary logic
  main() {
    # Early return for sourcing support
    if [ -n "${SOURCED:-}" ]
    then
      return 0
    fi

    # Argument parsing and main logic here
  }

  # Script entry point
  main "$@"
  ```
- **Usage function**: Always define and use a `usage()` function for help output
- **Main function**: Always wrap primary logic in a `main()` function and call `main "$@"`
- **Sourcing support**: Add `SOURCED` variable check at start of `main()` to allow sourcing for testing
- **Helper functions**: Extract complex logic into well-named helper functions to keep `main()` clean and readable
- **Sourcing support**: Add `SOURCED` variable check at start of `main()` to allow sourcing for testing
- **Helper functions**: Extract complex logic into well-named helper functions to keep `main()` clean and readable
- **Variable expansion**: Use braces `${VAR}` when variable is not used alone:
  ```bash
  # Good (standalone - braces optional):
  echo "$var"
  [ -n "$var" ]
  case "$var" in

  # Good (with braces when not alone - braces required):
  echo "my var=${var}"
  echo "path=${HOME}/bin"
  other_var=${var}

  # Avoid (missing braces when not alone):
  echo "my var=$var"
  echo "path=$HOME/bin"
  other_var=$var
  ```
- **POSIX Compatibility**:
  - **NEVER use `local` keyword in POSIX sh** - not supported (use positional parameters instead)
  - **`local` is fine in bash** - only avoid in POSIX sh scripts
  - Prefer POSIX-compliant constructs when targeting maximum portability
- **Control structures**: Place `then`, `do`, `else` on separate lines for readability:
  ```bash
  # Good:
  if [ "$condition" ]
  then
    action
  fi

  while [ "$condition" ]
  do
    action
  done

  # Avoid:
  if [ "$condition" ]; then action; fi
  ```
- **Alignment**: `then`, `do`, `else` should align with the same indentation as their control structure
- **Line endings**: One statement per line, avoid semicolon separators
  ```bash
  # Good:
  var1="one"
  var2="two"

  case "$var" in
    one)
      echo "xxxx"
      ;;
    two)
      echo "yyyy"
      ;;
  esac

  # Avoid:
  var1="one"; var2="two"
  case "$var" in one) echo "xxxx" ;; two) echo "yyyy" ;; esac
  ```
- **Boolean variables**: Use unset/empty for false and non-empty for true (typically "1"):
  ```bash
  # Good:
  THING=1
  if [ -n "${THING:-}" ]
  then
    echo "thing is enabled"
  fi

  # Also good (test for set/unset):
  if [ "${THING+set}" = "set" ]
  then
    echo "thing is set"
  fi

  # Good (test for false/unset):
  if [ -z "${THING:-}" ]
  then
    echo "thing is disabled or unset"
  fi

  # Avoid (string comparison):
  THING="true"
  if [ "$THING" = "true" ]
  then
    echo "thing is enabled"
  fi
  ```
- **Function exits**: Use `return` in functions, `exit` only from main script flow
- **Avoid exit in functions**: Never use `exit` within functions - use `return` instead
- **DRY principle**: Extract common patterns into functions to avoid repetition
- **Library usage**: Use `has_command` utility from `lib/utils.sh` instead of duplicating command checks
  ```bash
  # Good (POSIX-compatible):
  download_file() {
    # Use positional parameters: $1=url, $2=target, $3=downloader
    case "$3" in
      curl)
        curl -fsSL "$1" -o "$2"
        ;;
      wget)
        wget -q "$1" -O "$2"
        ;;
    esac
  }

  # Avoid (not POSIX sh):
  download_file() {
    local url="$1"  # ❌ 'local' not supported in POSIX sh (fine in bash)
    local target="$2"
  }
  ```

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

- **Flake**: Uses flake-parts for clean, modular structure
- **Dev shell**: Include all development dependencies with pre-commit hooks
- **NixOS module**: Provide systemd service configuration with security hardening
- **Package**: Self-contained package with Python dependencies
- **Docker**: Automated container image generation
- **Security**: Use proper systemd security features
- **Pre-commit**: Native pre-commit-hooks.nix integration with comprehensive checks

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
