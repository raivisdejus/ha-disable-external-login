"""Middleware to block external login attempts."""

from __future__ import annotations

import ipaddress
import logging
from collections.abc import Callable
from typing import Any

from aiohttp import web
from aiohttp.web import middleware

from .const import CONF_ENABLED, CONF_LOCAL_NETWORKS

_LOGGER = logging.getLogger(__name__)

BLOCKED_PATHS = {
    "/auth/login_flow",
    "/auth/authorize",
}

BLOCKED_HTML = """<!DOCTYPE html>
<html>
<head><title>Access Denied</title></head>
<body style="display:flex;justify-content:center;align-items:center;height:100vh;
margin:0;font-family:sans-serif;background:#fafafa;">
<div style="text-align:center;max-width:400px;padding:2em;">
<h1 style="color:#d32f2f;">Access Denied</h1>
<p>Login from external networks is disabled.</br>Please connect from your local network.</p>
</div>
</body>
</html>"""


def _is_local(remote: str | None, networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network]) -> bool:
    """Check if a remote address is within any of the configured local networks."""
    if remote is None:
        return False
    try:
        addr = ipaddress.ip_address(remote)
    except ValueError:
        return False
    return any(addr in network for network in networks)


def _is_login_path(path: str) -> bool:
    """Check if the request path is a login-related path that should be blocked."""
    if path == "/auth/authorize":
        return True
    if path == "/auth/login_flow":
        return True
    if path.startswith("/auth/login_flow/"):
        return True
    return False


def create_middleware(
    get_config: Callable[[], dict[str, Any] | None],
) -> Callable:
    """Create the external login blocking middleware."""

    @middleware
    async def block_external_login(
        request: web.Request,
        handler: Callable,
    ) -> web.StreamResponse:
        """Block login attempts from external networks."""
        config = get_config()

        # No-op if config is missing or disabled
        if config is None or not config.get(CONF_ENABLED, True):
            return await handler(request)

        # Only check login-related paths
        if not _is_login_path(request.path):
            return await handler(request)

        # Only block POST for login_flow, GET for authorize
        if request.path == "/auth/authorize" and request.method != "GET":
            return await handler(request)
        if request.path.startswith("/auth/login_flow") and request.method != "POST":
            return await handler(request)

        networks = config.get(CONF_LOCAL_NETWORKS, [])

        if _is_local(request.remote, networks):
            return await handler(request)

        _LOGGER.warning(
            "Blocked external login attempt from %s to %s",
            request.remote,
            request.path,
        )

        if request.path == "/auth/authorize":
            return web.Response(
                text=BLOCKED_HTML,
                content_type="text/html",
                status=403,
            )

        return web.json_response(
            {"message": "Login from external networks is disabled"},
            status=403,
        )

    return block_external_login
