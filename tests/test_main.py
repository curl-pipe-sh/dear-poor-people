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
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "poor-tools Web Installer" in response.text
    assert "Available endpoints:" in response.text


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

    # /installer should still use poor-installer
    response = client.get("/installer")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "poor-install" in response.text


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
        assert (
            "tcp_port_check" in response.text or "#!/usr/bin/env bash" in response.text
        )

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


def test_templating_disabled() -> None:
    """Test that templating can be disabled."""
    response = client.get("/install?no_templating=1")
    assert response.status_code == 200
    # With templating disabled, INCLUDE_FILE comments should remain as-is
    assert "INCLUDE_FILE:" in response.text


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
        assert "INCLUDE_FILE:" in response.text
    else:
        # Should have processed template
        assert "has_command" in response.text or "echo_success" in response.text
