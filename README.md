# poor-tools

A collection of quick-and-dirty shell hacks pretending to be real tools.
Made for situations where you can't install the proper thing (no internet, no package manager, no compiler, no patience).

They're small, ugly, and barely work — but sometimes that's enough.

## Web Installer

The web installer serves scripts via HTTP with optional templating support for easy deployment and installation.

### Quick Start

```bash
# Docker
docker run -p 7667:7667 ghcr.io/pschmitt/poor-tools

# Nix
nix run github:pschmitt/poor-tools#poor-tools-web

# Development
uv sync --all-extras --dev
python -m poor_installer_web.app
```

### Available Tools

- **poornmap** - Simple nmap alternative for basic port scanning
- **poorcurl** - curl-like wrapper using wget
- **poorcurl-openssl** - HTTPS client using openssl s_client
- **poorcolumn** - Minimal column(1) clone with basic -s/-t support
- **poorsocat** - Basic socat functionality

### Usage Examples

```bash
# Get info about available tools and installers
curl -sSL http://localhost:7667/

# List all available tools
curl -sSL http://localhost:7667/list

# Install all tools
curl -sSL http://localhost:7667/install | sh

# Generate and run tool-specific installer (recommended):
curl -sSL http://localhost:7667/curl/install | sh

# Install with options:
curl -sSL http://localhost:7667/curl/install | sh -s -- --dest /usr/local/bin --emulate

# Download individual tools directly:
curl -sSL http://localhost:7667/curl > ~/.local/bin/poorcurl
chmod +x ~/.local/bin/poorcurl

# All tool installers available:
curl -sSL http://localhost:7667/nmap/install | sh          # poornmap
curl -sSL http://localhost:7667/curl/install | sh          # poorcurl
curl -sSL http://localhost:7667/curl-openssl/install | sh  # poorcurl-openssl
curl -sSL http://localhost:7667/column/install | sh        # poorcolumn
curl -sSL http://localhost:7667/socat/install | sh         # poorsocat

# Disable templating (keeps INCLUDE_FILE comments as-is)
curl -sSL "http://localhost:7667/curl/install?no_templating=1" | sh
```

### CLI Options

```bash
python -m poor_installer_web.app --help
# or
poor-tools-web --help

Options:
  --bind-host BIND_HOST     Host to bind to (default: 127.0.0.1)
  --bind-port BIND_PORT     Port to bind to (default: 7667)
  --script-dir SCRIPT_DIR   Directory containing scripts to serve
```

### Environment Variables

- `BIND_HOST` - Host to bind to (default: 127.0.0.1)
- `BIND_PORT` - Port to bind to (default: 7667)

## Local Installation

Run `./poor-installer --dest /some/bin` to copy every tool into your own bin
directory. Useful flags:

- `--emulate` strips the `poor` prefix (so `poorcurl` becomes `curl`).
- `--clear` wipes the destination before installing.
- `--ignore NAME` or `--ignore 'pattern*'` skips specific tools.
- `--uninstall` removes the files we would install (respects the same flags).

You can also install a subset via globs: `./poor-installer --dest ~/.local/bin 'curl*'`.

## License

GPL-3.0, deal with it.
