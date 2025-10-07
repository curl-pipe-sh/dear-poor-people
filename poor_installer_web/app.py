"""Web installer for poor-tools."""

import argparse
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

app = FastAPI(
    title="poor-tools Web Installer",
    description="Web installer for poor-tools collection",
    version="0.1.0",
)


# Base directory containing the poor-tools - handle both dev and installed contexts
def get_default_script_dir() -> Path:
    """Get the default script directory, handling both dev and installed contexts."""
    # First try the directory where this script is located (dev context)
    script_dir = Path(__file__).parent.absolute()

    # Check if we have poor-tools scripts in this directory
    poor_tools = list(script_dir.glob("poor*"))
    if poor_tools and any(tool.is_file() for tool in poor_tools):
        return script_dir

    # If we're in an installed context, look for the site-packages location
    # The poor_installer_web module is in a subdirectory, but templates/lib are in parent
    import poor_installer_web

    package_dir = Path(poor_installer_web.__file__).parent
    site_packages_dir = package_dir.parent

    # Check if templates directory exists at site-packages level
    if (site_packages_dir / "templates").exists():
        return site_packages_dir

    # Check if we're in a development context where everything is in parent directory
    parent_dir = script_dir.parent
    if (parent_dir / "templates").exists():
        return parent_dir

    # Fallback to script directory
    return script_dir


BASE_DIR = get_default_script_dir()

# Configuration that can be overridden via CLI args
SCRIPT_DIR = BASE_DIR


def is_script_file(file_path: Path) -> bool:
    """Check if a file is a valid script file."""
    if not file_path.is_file():
        return False

    try:
        # Read first line to check for shebang
        with file_path.open("r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            return first_line.startswith("#!")
    except (UnicodeDecodeError, PermissionError):
        return False


def discover_tools() -> list[str]:
    """Dynamically discover available tools in the script directory."""
    tools = []

    # Look for files that look like poor-tools scripts
    for file_path in SCRIPT_DIR.iterdir():
        if is_script_file(file_path):
            name = file_path.name
            # Skip certain files
            if name in {"main.py"} or name.startswith("."):
                continue
            tools.append(name)

    return sorted(tools)


def get_tool_description(tool_name: str) -> str:
    """Extract description from a tool script file."""
    file_path = SCRIPT_DIR / tool_name
    if not file_path.exists():
        return ""

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f):
                # Only check first 10 lines for performance
                if line_num >= 10:
                    break

                line = line.strip()
                if line.startswith("# description:"):
                    return line[len("# description:") :].strip()

                # Also check for the format "# toolname — description"
                if line.startswith(f"# {tool_name} —") or line.startswith(
                    f"# {tool_name} -"
                ):
                    return line.split("—", 1)[-1].split("-", 1)[-1].strip()
    except Exception:
        pass

    return ""


def get_tool_icon(tool_name: str) -> str:
    """Extract icon from a tool script file."""
    file_path = SCRIPT_DIR / tool_name
    if not file_path.exists():
        return "mdi:wrench"  # Default icon

    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f):
                # Only check first 10 lines for performance
                if line_num >= 10:
                    break

                line = line.strip()
                if line.startswith("# icon:"):
                    icon = line[len("# icon:") :].strip()
                    # Ensure it starts with mdi: if not already specified
                    if not icon.startswith("mdi:"):
                        icon = f"mdi:{icon}"
                    return icon
    except Exception:
        pass

    return "mdi:wrench"  # Default icon


def normalize_tool_name(tool_name: str) -> str | None:
    """Normalize tool name and return the canonical script name."""
    discovered_tools = discover_tools()

    # Direct match
    if tool_name in discovered_tools:
        return tool_name

    # Try with poor prefix
    poor_name = f"poor{tool_name}"
    if poor_name in discovered_tools:
        return poor_name

    # Try without poor prefix
    if tool_name.startswith("poor"):
        no_poor_name = tool_name[4:]  # Remove "poor" prefix
        for tool in discovered_tools:
            if tool == no_poor_name or tool == f"poor{no_poor_name}":
                return tool

    return None


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


def is_cli_user_agent(user_agent: str) -> bool:
    """Check if the user agent is a CLI tool like curl, wget, etc."""
    if not user_agent:
        return True  # Default to CLI if no user agent

    cli_agents = [
        "curl/",
        "wget/",
        "httpie/",
        "lwp-request",
        "python-requests/",
        "python-urllib",
        "go-http-client",
        "rust-hyper",
        "libcurl",
    ]

    user_agent_lower = user_agent.lower()
    return any(agent in user_agent_lower for agent in cli_agents)


def load_template(template_name: str) -> str:
    """Load a template file from the assets directory."""
    template_path = Path(__file__).parent / "assets" / "templates" / template_name
    if not template_path.exists():
        raise HTTPException(
            status_code=500, detail=f"Template '{template_name}' not found"
        )
    return template_path.read_text(encoding="utf-8")


def load_static_file(file_name: str) -> str:
    """Load a static file from the assets directory."""
    static_path = Path(__file__).parent / "assets" / "static" / file_name
    if not static_path.exists():
        raise HTTPException(
            status_code=500, detail=f"Static file '{file_name}' not found"
        )
    return static_path.read_text(encoding="utf-8")


def generate_tool_installer(
    tool_name: str, server_url: str, no_templating: bool = False
) -> str:
    """Generate a tool-specific installer script."""
    template_path = SCRIPT_DIR / "templates" / "tool-installer.sh"

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Tool installer template not found")

    try:
        content = template_path.read_text(encoding="utf-8")

        # Replace template variables with angle bracket syntax
        content = content.replace("<TOOL_NAME>", tool_name)
        content = content.replace("<SERVER_URL>", server_url)

        # If tool_name is "all", we need to update the tool list dynamically
        if tool_name == "all":
            tools = discover_tools()
            # Filter out non-poor-tools and special files
            tool_names = []
            for tool in tools:
                if tool.startswith("poor"):
                    # Remove "poor" prefix for the tool list
                    tool_names.append(tool[4:])
                else:
                    tool_names.append(tool)

            # Replace the hardcoded tool list
            tools_str = " ".join(tool_names)
            content = content.replace(
                'TOOLS="nmap curl curl-openssl column socat"', f'TOOLS="{tools_str}"'
            )

        # Process includes if templating is enabled
        if not no_templating:
            content = process_includes(content, SCRIPT_DIR)

        return content
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate installer: {str(e)}"
        ) from e


def process_includes(content: str, base_dir: Path) -> str:
    """Process INCLUDE_FILE directives in the content.

    Replaces lines like:
    - '# INCLUDE_FILE: lib/echo.sh' with the actual file content (old format)
    - 'source lib/echo.sh # <TEMPLATE>' with the actual file content (new format)
    - '. lib/echo.sh # <TEMPLATE>' with the actual file content (POSIX format)
    """
    lines = content.split("\n")
    result_lines = []

    for line in lines:
        # Check for old-style include directive
        if line.strip().startswith("# INCLUDE_FILE:"):
            include_path = line.strip()[len("# INCLUDE_FILE:") :].strip()
            file_path = base_dir / include_path

            if file_path.exists():
                try:
                    include_content = file_path.read_text(encoding="utf-8")
                    # Remove any trailing newlines and add content
                    include_content = include_content.rstrip()
                    if include_content:
                        result_lines.append(include_content)
                except Exception:
                    # If we can't read the file, keep the original line
                    result_lines.append(line)
            else:
                # If file doesn't exist, keep the original line
                result_lines.append(line)

        # Check for new-style template directives
        elif "# <TEMPLATE>" in line:
            # Extract the part before # <TEMPLATE>
            source_part = line.split("# <TEMPLATE>")[0].strip()

            # Handle both 'source' and '.' (POSIX) variants
            if source_part.startswith("source "):
                include_path = source_part[len("source ") :].strip()
            elif source_part.startswith(". "):
                include_path = source_part[len(". ") :].strip()
            else:
                # Not a recognized pattern, keep original line
                result_lines.append(line)
                continue

            file_path = base_dir / include_path

            if file_path.exists():
                try:
                    include_content = file_path.read_text(encoding="utf-8")
                    # Remove any trailing newlines and add content
                    include_content = include_content.rstrip()
                    if include_content:
                        result_lines.append(include_content)
                except Exception:
                    # If we can't read the file, keep the original line
                    result_lines.append(line)
            else:
                # If file doesn't exist, keep the original line
                result_lines.append(line)
        else:
            # Regular line, keep as-is
            result_lines.append(line)

    return "\n".join(result_lines)


def apply_common_placeholders(content: str, server_url: str) -> str:
    """Apply standard placeholder replacements for scripts."""

    return content.replace("<BASE_URL>", server_url)


def get_file_content(filename: str, no_templating: bool = False) -> str:
    """Get the content of a file, optionally processing includes."""
    file_path = SCRIPT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    try:
        content = file_path.read_text(encoding="utf-8")

        # Process includes if templating is enabled
        if not no_templating:
            content = process_includes(content, SCRIPT_DIR)

        return content
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read file '{filename}': {str(e)}"
        ) from e


@app.get("/")
async def get_root(request: Request, no_templating: str | None = None) -> Response:
    """Serve information about available tools and endpoints."""
    server_url = get_server_url(request)
    tools = discover_tools()
    user_agent = request.headers.get("user-agent", "")

    # If it's a CLI tool, return plain text response
    if is_cli_user_agent(user_agent):
        # Generate tool list dynamically
        tool_links = []
        installer_links = []

        for tool in tools:
            # Create display name (remove poor prefix for display if present, except for "poor" itself)
            if tool == "poor":
                display_name = "poor"
            else:
                display_name = (
                    tool.replace("poor", "", 1) if tool.startswith("poor") else tool
                )
            tool_links.append(f"- {server_url}/{display_name} (alias: /{tool})")
            installer_links.append(f"- {server_url}/{display_name}/install")

        info_content = f"""# poor-tools Web Installer

Available endpoints:

## Individual Tools (direct download):
{chr(10).join(tool_links)}

## Tool Installers (generates installer script):
{chr(10).join(installer_links)}

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

    # For web browsers, return HTML using templates
    # Generate tools cards HTML
    tools_cards_html = ""
    for i, tool in enumerate(tools):
        # Create display name (remove poor prefix for display if present, except for "poor" itself)
        if tool == "poor":
            display_name = "poor"
        else:
            display_name = (
                tool.replace("poor", "", 1) if tool.startswith("poor") else tool
            )
        description = get_tool_description(tool)
        icon = get_tool_icon(tool)
        delay = i * 100  # Stagger animations

        description_html = (
            f'<p class="tool-description">{description}</p>' if description else ""
        )

        # Generate command snippets
        run_command = f"curl -sSL {server_url}/{display_name} | sh -s -- --help"
        install_command = f"curl -sSL {server_url}/{display_name}/install | sh"

        tools_cards_html += f"""
        <div class="tool-card" style="animation-delay: {delay}ms">
          <div class="tool-header">
            <iconify-icon icon="{icon}" class="tool-icon"></iconify-icon>
            <h3 class="tool-name">{display_name}</h3>
          </div>
          {description_html}
          <div class="command-snippets">
            <div class="command-snippet">
              <span class="command-label">Run directly:</span>
              <div class="command-box">
                <pre class="command-code" data-action="run"><code class="language-bash">{run_command}</code></pre>
                <button class="clipboard-btn" onclick="copyToClipboard(this, '{run_command}', 'run', '{display_name}')" title="Copy command">
                  <iconify-icon icon="mdi:content-copy"></iconify-icon>
                </button>
              </div>
            </div>
            <div class="command-snippet">
              <span class="command-label">Install locally:</span>
              <div class="command-box">
                <pre class="command-code" data-action="install"><code class="language-bash">{install_command}</code></pre>
                <button class="clipboard-btn" onclick="copyToClipboard(this, '{install_command}', 'install', '{display_name}')" title="Copy command">
                  <iconify-icon icon="mdi:content-copy"></iconify-icon>
                </button>
              </div>
            </div>
          </div>
        </div>"""

    # Generate featured commands HTML - now empty since we're removing Quick Start
    commands_html = ""

    # Load template and static files
    template_content = load_template("index.html")
    css_content = load_static_file("style.css")
    js_content = load_static_file("script.js")

    # Replace template variables
    html_content = template_content.replace("{{ css_content }}", css_content)
    html_content = html_content.replace("{{ js_content }}", js_content)
    html_content = html_content.replace("{{ commands_html }}", commands_html)
    html_content = html_content.replace("{{ tools_cards_html }}", tools_cards_html)

    return HTMLResponse(content=html_content)


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
    tools = discover_tools()

    # Generate tool list dynamically
    tool_links = []
    installer_links = []

    for tool in tools:
        # Create display name (remove poor prefix for display if present, except for "poor" itself)
        if tool == "poor":
            display_name = "poor"
        else:
            display_name = (
                tool.replace("poor", "", 1) if tool.startswith("poor") else tool
            )
        tool_links.append(f"- {server_url}/{display_name} (alias: /{tool})")
        installer_links.append(f"- {server_url}/{display_name}/install")

    tools_list = f"""# poor-tools Available Tools

Available tools and endpoints:

## Direct Tool Downloads:
{chr(10).join(tool_links)}

## Tool Installers (generates installer script):
{chr(10).join(installer_links)}

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


async def _serve_installer(
    request: Request, no_templating: str | None = None
) -> Response:
    """Common installer handler."""
    content = get_file_content("poor", no_templating == "1")

    if no_templating != "1":
        server_url = get_server_url(request)
        content = apply_common_placeholders(content, server_url)

    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


@app.get("/installer", response_class=PlainTextResponse)
async def get_installer(request: Request, no_templating: str | None = None) -> Response:
    """Serve the poor script with install functionality."""
    return await _serve_installer(request, no_templating)


# Catch-all for /install* paths
@app.get("/install{path:path}", response_class=PlainTextResponse)
async def get_installer_with_path(
    request: Request, path: str, no_templating: str | None = None
) -> Response:
    """Serve the poor script with install functionality for any /install* path."""
    return await _serve_installer(request, no_templating)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Dynamic tool endpoint handler
@app.get("/{tool_name}/install", response_class=PlainTextResponse)
async def get_tool_installer(
    tool_name: str, request: Request, no_templating: str | None = None
) -> Response:
    """Generate installer script for a specific tool."""
    # Normalize tool name
    canonical_name = normalize_tool_name(tool_name)

    if canonical_name is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    server_url = get_server_url(request)
    content = generate_tool_installer(canonical_name, server_url, no_templating == "1")
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


# Dynamic tool script handler
@app.get("/{tool_name}", response_class=PlainTextResponse)
async def get_tool_script(
    tool_name: str, request: Request, no_templating: str | None = None
) -> Response:
    """Serve a tool script dynamically."""
    # Handle special cases first
    if tool_name in {"health", "list", "install", "installer"}:
        raise HTTPException(status_code=404, detail="Reserved endpoint")

    # Normalize tool name
    canonical_name = normalize_tool_name(tool_name)

    if canonical_name is None:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    content = get_file_content(canonical_name, no_templating == "1")

    if no_templating != "1":
        server_url = get_server_url(request)
        content = apply_common_placeholders(content, server_url)
    return PlainTextResponse(
        content=content, headers={"Content-Type": "text/plain; charset=utf-8"}
    )


def main() -> None:
    """Main entry point for the CLI script."""

    global SCRIPT_DIR

    parser = argparse.ArgumentParser(description="poor-tools Web Installer")
    parser.add_argument(
        "--bind-host",
        default=os.getenv("BIND_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--bind-port",
        type=int,
        default=int(os.getenv("BIND_PORT", "7667")),
        help="Port to bind to (default: 7667)",
    )
    parser.add_argument(
        "--script-dir",
        type=Path,
        default=BASE_DIR,
        help="Directory containing scripts to serve (default: current directory)",
    )

    args = parser.parse_args()

    # Update the global script directory
    SCRIPT_DIR = args.script_dir.resolve()

    if not SCRIPT_DIR.exists():
        print(f"Error: Script directory {SCRIPT_DIR} does not exist")
        return

    uvicorn.run(app, host=args.bind_host, port=args.bind_port)


if __name__ == "__main__":
    main()
