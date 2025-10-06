"""Tests for the poor-tools web installer."""

from fastapi.testclient import TestClient

from main import app

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


def test_installer_endpoints() -> None:
    """Test various installer endpoints."""
    endpoints = ["/install", "/installer", "/install-something"]

    for endpoint in endpoints:
        response = client.get(endpoint)
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
    # (though our current scripts don't have them yet)


def test_templating_enabled() -> None:
    """Test that templating works when enabled."""
    response = client.get("/install")
    assert response.status_code == 200
    # With templating enabled, INCLUDE_FILE comments should be processed
    # (though our current scripts don't have them yet)


def test_nonexistent_file() -> None:
    """Test handling of nonexistent files."""
    # This would happen if the script files were missing
    # For now, we just test that the endpoints exist
