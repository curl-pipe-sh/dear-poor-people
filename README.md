# poor-tools

A collection of quick-and-dirty shell hacks pretending to be real tools.
Made for situations where you can't install the proper thing (no internet, no package manager, no compiler, no patience).

They're small, ugly, and barely work — but sometimes that's enough.

## Web Installer

The web installer serves scripts via HTTP with optional templating support for easy deployment and installation.

### Quick Start

```bash
# Docker
docker run -p 7667:7667 ghcr.io/curl-pipe-sh/poor-tools

# Nix
nix run github:curl-pipe-sh/poor-tools#poor-tools-web

# Development
uv sync --all-extras --dev
python -m poor_installer_web.app
```

### Available Tools

- **poornmap** - Simple nmap alternative for basic port scanning
- **poor** - Busybox-style wrapper that fetches and runs other poor-tools
- **poorcurl** - curl-like wrapper using wget
- **poorcurl-openssl** - HTTPS client using openssl s_client
- **poorcolumn** - Minimal column(1) clone with basic -s/-t support
- **poorsocat** - Basic socat functionality

### Usage Examples

```bash
# Run a tool without installing it
./poor curl https://example.com

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

# Fetch and run tools through the multiplexer
curl -sSL http://localhost:7667/poor | sh -s -- curl https://example.com
curl -sSL http://localhost:7667/poor | sh -s -- install --dest ~/.local/bin

# Install the multiplexer itself and use busybox-style symlinks
curl -sSL http://localhost:7667/poor > ~/.local/bin/poor
chmod +x ~/.local/bin/poor
ln -sf ~/.local/bin/poor ~/.local/bin/curl
curl https://example.com

# All tool installers available:
curl -sSL http://localhost:7667/nmap/install | sh          # poornmap
curl -sSL http://localhost:7667/curl/install | sh          # poorcurl
curl -sSL http://localhost:7667/curl-openssl/install | sh  # poorcurl-openssl
curl -sSL http://localhost:7667/column/install | sh        # poorcolumn
curl -sSL http://localhost:7667/socat/install | sh         # poorsocat

# Disable templating (keeps # <TEMPLATE> comments as-is)
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

Run `./poor install --dest /some/bin` (or the legacy `./poor-installer`) to
copy every tool into your own bin directory. Useful flags:

- `--emulate` strips the `poor` prefix (so `poorcurl` becomes `curl`).
- `--clear` wipes the destination before installing.
- `--ignore NAME` or `--ignore 'pattern*'` skips specific tools.
- `--uninstall` removes the files we would install (respects the same flags).

You can also install a subset via globs: `./poor-installer --dest ~/.local/bin 'curl*'`.

## poor multiplexer

The new `poor` script acts as the front-door to the entire toolbox:

```bash
# Run any tool directly
poor curl https://example.com
poor nmap -p 22 example.com

# Same behaviour through symlinks
ln -s poor poorcurl
./poorcurl --help

# Install tools using the web installer wrapper
poor install --dest ~/.local/bin
```

It supports a few environment variables for customization:

- `POOR_BASE_URL` — override the server or directory used to fetch tools
- `POOR_TOOL_DIR` — point at an existing directory of poor scripts
- `POOR_CACHE_DIR` — location to store downloaded copies (defaults to XDG cache)
- `POOR_DOWNLOADER` — force `curl` or `wget`
- `POOR_REFRESH=1` — always redownload before running a tool
- `POOR_NO_CACHE=1` — ignore existing cached copies for a single invocation

When retrieved from the web installer the script automatically targets the
serving host, so `curl http://localhost:7667/poor | sh -s -- curl example.com`
works without any manual configuration.

## License

GPL-3.0, deal with it.
