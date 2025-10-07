"""Tests for the poor-tools web installer."""

import pytest
from fastapi.testclient import TestClient

from poor_installer_web import app

client = TestClient(app)


def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint() -> None:
    """Test the root endpoint returns info."""
    # Test CLI user agent (curl)
    response = client.get("/", headers={"User-Agent": "curl/7.68.0"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "poor-tools Web Installer" in response.text
    assert "Available endpoints:" in response.text

    # Test browser user agent
    response = client.get(
        "/",
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert "poor-tools" in response.text
    assert "Portable shell tools" in response.text


def test_cli_user_agent_detection() -> None:
    """Test CLI user agent detection."""
    from poor_installer_web.app import is_cli_user_agent

    # CLI tools should return True
    assert is_cli_user_agent("curl/7.68.0") is True
    assert is_cli_user_agent("Wget/1.21.3") is True
    assert is_cli_user_agent("python-requests/2.25.1") is True
    assert is_cli_user_agent("HTTPie/2.4.0") is True
    assert is_cli_user_agent("") is True  # Empty defaults to CLI

    # Browser user agents should return False
    assert (
        is_cli_user_agent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36") is False
    )
    assert is_cli_user_agent("Safari/537.36") is False
    assert is_cli_user_agent("Chrome/91.0.4472.124") is False


def test_tool_description_parsing() -> None:
    """Test tool description parsing from script files."""
    from poor_installer_web.app import get_tool_description

    # Test with actual tool files that should have descriptions
    # We added descriptions to these files earlier
    description = get_tool_description("poorcurl")
    assert "curl, but uses wget behind the scenes" in description

    description = get_tool_description("poorcolumn")
    assert "minimal column(1) clone" in description

    # Test with non-existent file
    description = get_tool_description("non-existent-tool")
    assert description == ""


def test_tool_icon_parsing() -> None:
    """Test tool icon parsing from script files."""
    from poor_installer_web.app import get_tool_icon

    # Test with actual tool files that should have icons
    icon = get_tool_icon("poorcurl")
    assert icon == "mdi:download"

    icon = get_tool_icon("poorcolumn")
    assert icon == "mdi:table"

    icon = get_tool_icon("poornmap")
    assert icon == "mdi:network-outline"

    # Test with non-existent file (should return default)
    icon = get_tool_icon("non-existent-tool")
    assert icon == "mdi:wrench"


def test_list_endpoint() -> None:
    """Test the list tools endpoint."""
    response = client.get("/list")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "Available tools and endpoints" in response.text
    assert "/nmap" in response.text
    assert "/curl/install" in response.text


def test_head_root_endpoint() -> None:
    """Test HEAD request to root returns list."""
    response = client.head("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_installer_endpoints() -> None:
    """Test various installer endpoints."""
    # /install should now use tool-installer.sh template with "all" tools
    response = client.get("/install")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "all installer" in response.text
    assert "Installing all poor-tools" in response.text

    # /installer should now use poor with install command  
    response = client.get("/installer")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "poor" in response.text and "install" in response.text


def test_tool_installer_endpoints() -> None:
    """Test tool-specific installer endpoints."""
    tool_installers = [
        "/nmap/install",
        "/curl/install",
        "/curl-openssl/install",
        "/column/install",
        "/socat/install",
    ]

    for endpoint in tool_installers:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        # Should contain the generated installer script
        assert "installer —" in response.text
        assert "DEST=" in response.text
        assert "usage()" in response.text


def test_all_tool_endpoints() -> None:
    """Test all tool endpoints with their aliases."""
    # Test nmap endpoints
    for endpoint in ["/nmap", "/poornmap"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "detect_netcat_tool" in response.text

    # Test curl endpoints
    for endpoint in ["/curl", "/poorcurl"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "curl-like wrapper" in response.text or "wget" in response.text

    # Test curl-openssl endpoints
    for endpoint in ["/curl-openssl", "/poorcurl-openssl"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Test column endpoints
    for endpoint in ["/column", "/poorcolumn"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Test socat endpoints
    for endpoint in ["/socat", "/poorsocat"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    # Test poor multiplexer endpoint
    response = client.get("/poor")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "<BASE_URL>" not in response.text
    assert 'DEFAULT_BASE_URL="http://testserver"' in response.text

    response = client.get("/poor", params={"no_templating": "1"})
    assert response.status_code == 200
    assert "<BASE_URL>" in response.text


def test_templating_disabled() -> None:
    """Test that templating can be disabled."""
    response = client.get("/install?no_templating=1")
    assert response.status_code == 200
    # With templating disabled, the source xxx # <TEMPLATE> comments should
    # remain as-is
    assert "# <TEMPLATE>" in response.text


def test_templating_enabled() -> None:
    """Test that templating works when enabled."""
    response = client.get("/install")
    assert response.status_code == 200
    # With templating enabled, INCLUDE_FILE comments should be processed
    assert "BEGIN INCLUDE:" in response.text or "has_command" in response.text


def test_tool_aliases() -> None:
    """Test that tool aliases work correctly."""
    # Test that both /curl and /poorcurl return the same content
    response1 = client.get("/curl")
    response2 = client.get("/poorcurl")
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.text == response2.text

    # Test that both /column and /poorcolumn work
    response1 = client.get("/column")
    response2 = client.get("/poorcolumn")
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.text == response2.text


def test_server_url_detection() -> None:
    """Test that server URL is correctly detected from request headers."""
    response = client.get("/install", headers={"host": "example.com:8080"})
    assert response.status_code == 200
    assert "http://example.com:8080" in response.text


@pytest.mark.parametrize("no_templating", ["1", "0", None])
def test_templating_parameter(no_templating: str | None) -> None:
    """Test templating parameter works correctly."""
    params = {"no_templating": no_templating} if no_templating else {}
    response = client.get("/install", params=params)
    assert response.status_code == 200

    if no_templating == "1":
        # Should contain raw template
        assert "# <TEMPLATE>" in response.text
    else:
        # Should have processed template
        assert "has_command" in response.text or "echo_success" in response.text
