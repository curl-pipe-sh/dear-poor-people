"""Web installer for poor-tools."""

import os
import re
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

app = FastAPI(
    title="poor-tools Web Installer",
    description="Web installer for poor-tools collection",
    version="0.1.0",
)

# Base directory containing the poor-tools
BASE_DIR = Path(__file__).parent


def get_server_url(request: Request) -> str:
    """Get the server URL from the request."""
    # Get the host header
    host = request.headers.get("host", "localhost:7667")

    # Determine scheme - check for forwarded headers from reverse proxies
    scheme = "http"
    if (
        request.headers.get("x-forwarded-proto") == "https"
        or request.headers.get("x-forwarded-ssl") == "on"
        or request.url.scheme == "https"
    ):
        scheme = "https"

    return f"{scheme}://{host}"


def generate_tool_installer(
    tool_name: str, server_url: str, no_templating: bool = False
) -> str:
    """Generate a tool-specific installer script."""
    template_path = BASE_DIR / "templates" / "tool-installer.sh"

    if not template_path.exists():
        return "Error: tool installer template not found"

    try:
        content = template_path.read_text(encoding="utf-8")

        # Replace template variables with angle bracket syntax
        content = content.replace("<TOOL_NAME>", tool_name)
        content = content.replace("<SERVER_URL>", server_url)

        # Process includes if templating is enabled
        if not no_templating:
            content = process_includes(content, BASE_DIR)

        return content
    except Exception:
        return "Error: failed to generate installer"


def process_includes(content: str, base_dir: Path) -> str:
    """Process INCLUDE_FILE directives in the content.

    Replaces lines like '# INCLUDE_FILE: lib/echo.sh' with the actual file content.
    """
    lines = content.split("\n")
    processed_lines = []

    for line in lines:
        # Match pattern like: # INCLUDE_FILE: lib/echo.sh
        include_match = re.match(r"^\s*#\s*INCLUDE_FILE:\s*(.+?)\s*$", line)
        if include_match:
            include_path = include_match.group(1).strip()
            include_file = base_dir / include_path

            if include_file.exists():
                try:
                    include_content = include_file.read_text(encoding="utf-8")
                    # Add a comment showing what was included
                    processed_lines.append(f"# BEGIN INCLUDE: {include_path}")
                    processed_lines.append(include_content.rstrip())
                    processed_lines.append(f"# END INCLUDE: {include_path}")
                except Exception:
                    # If we can't read the file, keep the original line
                    processed_lines.append(line)
            else:
                # If file doesn't exist, keep the original line
                processed_lines.append(line)
        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


def get_file_content(filename: str, no_templating: bool = False) -> str | None:
    """Get the content of a file, optionally processing includes."""
    file_path = BASE_DIR / filename

    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding="utf-8")

        if not no_templating:
            content = process_includes(content, BASE_DIR)

        return content
    except Exception:
        return None


@app.get("/", response_class=PlainTextResponse)
async def get_root(request: Request, no_templating: str | None = None) -> Response:
    """Serve information about available tools and endpoints."""
    server_url = get_server_url(request)

    info_content = f"""# poor-tools Web Installer

Available endpoints:

## Individual Tools (direct download):
- {server_url}/nmap (or /poornmap)
- {server_url}/curl (or /poorcurl)
- {server_url}/curl-openssl (or /poorcurl-openssl)
- {server_url}/column (or /poorcolumn)
- {server_url}/socat (or /poorsocat)

## Tool Installers (generates installer script):
- {server_url}/nmap/install
- {server_url}/curl/install
- {server_url}/curl-openssl/install
- {server_url}/column/install
- {server_url}/socat/install

## Bundle Installer:
- {server_url}/install (or /installer)

## Usage Examples:

# Install curl directly:
curl -sSL {server_url}/curl > ~/.local/bin/poorcurl && chmod +x ~/.local/bin/poorcurl

# Generate and run installer for curl:
curl -sSL {server_url}/curl/install | sh

# Install with options:
curl -sSL {server_url}/curl/install | sh -s -- --dest /usr/local/bin --emulate

# Install all tools:
curl -sSL {server_url}/install | sh

All endpoints support ?no_templating=1 to disable include processing.
"""

    return PlainTextResponse(
        content=info_content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/nmap", response_class=PlainTextResponse)
@app.get("/poornmap", response_class=PlainTextResponse)
async def get_poornmap(no_templating: str | None = None) -> Response:
    """Serve the poornmap script."""
    content = get_file_content("poornmap", no_templating == "1")

    if content is None:
        return Response(
            content="Error: poornmap not found",
            status_code=404,
            media_type="text/plain",
        )

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/curl", response_class=PlainTextResponse)
@app.get("/poorcurl", response_class=PlainTextResponse)
async def get_poorcurl(no_templating: str | None = None) -> Response:
    """Serve the poorcurl script."""
    content = get_file_content("poorcurl", no_templating == "1")

    if content is None:
        return Response(
            content="Error: poorcurl not found",
            status_code=404,
            media_type="text/plain",
        )

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/curl-openssl", response_class=PlainTextResponse)
@app.get("/poorcurl-openssl", response_class=PlainTextResponse)
async def get_poorcurl_openssl(no_templating: str | None = None) -> Response:
    """Serve the poorcurl-openssl script."""
    content = get_file_content("poorcurl-openssl", no_templating == "1")

    if content is None:
        return Response(
            content="Error: poorcurl-openssl not found",
            status_code=404,
            media_type="text/plain",
        )

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/column", response_class=PlainTextResponse)
@app.get("/poorcolumn", response_class=PlainTextResponse)
async def get_poorcolumn(no_templating: str | None = None) -> Response:
    """Serve the poorcolumn script."""
    content = get_file_content("poorcolumn", no_templating == "1")

    if content is None:
        return Response(
            content="Error: poorcolumn not found",
            status_code=404,
            media_type="text/plain",
        )

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/socat", response_class=PlainTextResponse)
@app.get("/poorsocat", response_class=PlainTextResponse)
async def get_poorsocat(no_templating: str | None = None) -> Response:
    """Serve the poorsocat script."""
    content = get_file_content("poorsocat", no_templating == "1")

    if content is None:
        return Response(
            content="Error: poorsocat not found",
            status_code=404,
            media_type="text/plain",
        )

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/install", response_class=PlainTextResponse)
@app.get("/install/", response_class=PlainTextResponse)
async def get_install_all(
    request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for all tools."""
    server_url = get_server_url(request)
    content = generate_tool_installer("all", server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/list", response_class=PlainTextResponse)
@app.head("/", response_class=PlainTextResponse)
async def list_tools(request: Request) -> Response:
    """List available tools in plain text format."""
    server_url = get_server_url(request)

    tools_list = f"""# poor-tools Available Tools

Available tools and endpoints:

## Direct Tool Downloads:
- {server_url}/nmap (alias: /poornmap)
- {server_url}/curl (alias: /poorcurl)
- {server_url}/curl-openssl (alias: /poorcurl-openssl)
- {server_url}/column (alias: /poorcolumn)
- {server_url}/socat (alias: /poorsocat)

## Tool Installers (generates installer script):
- {server_url}/nmap/install
- {server_url}/curl/install
- {server_url}/curl-openssl/install
- {server_url}/column/install
- {server_url}/socat/install

## Batch Installer:
- {server_url}/install (installs all tools)

## Usage Examples:

# Download and run a tool directly:
curl -sSL {server_url}/curl | sh

# Install a tool to local bin:
curl -sSL {server_url}/curl/install | sh

# Install all tools:
curl -sSL {server_url}/install | sh

# Install with custom destination:
curl -sSL {server_url}/curl/install | sh -s -- --dest /usr/local/bin
"""

    return Response(content=tools_list, media_type="text/plain; charset=utf-8")


@app.get("/installer", response_class=PlainTextResponse)
async def get_installer(no_templating: str | None = None) -> Response:
    """Serve the poor-installer script."""
    content = get_file_content("poor-installer", no_templating == "1")

    if content is None:
        return Response(
            content="Error: poor-installer not found",
            status_code=404,
            media_type="text/plain",
        )

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


# Tool-specific installers
@app.get("/nmap/install", response_class=PlainTextResponse)
@app.get("/poornmap/install", response_class=PlainTextResponse)
async def get_nmap_installer(
    request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for nmap."""
    server_url = get_server_url(request)
    content = generate_tool_installer("nmap", server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/curl/install", response_class=PlainTextResponse)
@app.get("/poorcurl/install", response_class=PlainTextResponse)
async def get_curl_installer(
    request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for curl."""
    server_url = get_server_url(request)
    content = generate_tool_installer("curl", server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/curl-openssl/install", response_class=PlainTextResponse)
@app.get("/poorcurl-openssl/install", response_class=PlainTextResponse)
async def get_curl_openssl_installer(
    request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for curl-openssl."""
    server_url = get_server_url(request)
    content = generate_tool_installer("curl-openssl", server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/column/install", response_class=PlainTextResponse)
@app.get("/poorcolumn/install", response_class=PlainTextResponse)
async def get_column_installer(
    request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for column."""
    server_url = get_server_url(request)
    content = generate_tool_installer("column", server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/socat/install", response_class=PlainTextResponse)
@app.get("/poorsocat/install", response_class=PlainTextResponse)
async def get_socat_installer(
    request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for socat."""
    server_url = get_server_url(request)
    content = generate_tool_installer("socat", server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


# Catch-all for /install* paths
@app.get("/install{path:path}", response_class=PlainTextResponse)
async def get_installer_with_path(
    path: str, no_templating: str | None = None
) -> Response:
    """Serve the poor-installer script for any /install* path."""
    return await get_installer(no_templating)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import os

    import uvicorn

    bind_host = os.getenv("BIND_HOST", "127.0.0.1")
    bind_port = int(os.getenv("BIND_PORT", "7667"))

    uvicorn.run(app, host=bind_host, port=bind_port)
