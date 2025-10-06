# poor-tools

A collection of quick-and-dirty shell hacks pretending to be real tools.
Made for situations where you can't install the proper thing (no internet, no package manager, no compiler, no patience).

They're small, ugly, and barely work — but sometimes that's enough.

## Web Installer

The web installer serves scripts via HTTP with optional templating support.

### Quick Start

```bash
# Docker
docker run -p 7667:7667 ghcr.io/pschmitt/poor-tools

# Nix
nix run github:pschmitt/poor-tools#poor-tools-web

# Development
uv sync --all-extras --dev
python main.py
```

### Usage

```bash
# Get info about available tools and installers
curl -sSL http://localhost:7667/

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

## Installing the bundle

Run `./poor-installer --dest /some/bin` to copy every tool into your own bin
directory. Useful flags:

- `--emulate` strips the `poor` prefix (so `poorcurl` becomes `curl`).
- `--clear` wipes the destination before installing.
- `--ignore NAME` or `--ignore 'pattern*'` skips specific tools.
- `--uninstall` removes the files we would install (respects the same flags).

You can also install a subset via globs: `./poor-installer --dest ~/.local/bin 'curl*'`.

## License

GPL-3.0, deal with it.
