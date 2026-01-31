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
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Access Denied</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    background: #f5f5f5;
    color: #333;
    padding: 1rem;
  }
  .card {
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    max-width: 420px;
    width: 100%;
    padding: 2.5rem 2rem;
    text-align: center;
  }
  .icon {
    width: 72px;
    height: 72px;
    margin: 0 auto 1.5rem;
    background: #fce4ec;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .icon svg { width: 36px; height: 36px; }
  h1 {
    font-size: 1.375rem;
    font-weight: 600;
    color: #c62828;
    margin-bottom: 0.75rem;
  }
  p {
    font-size: 0.975rem;
    line-height: 1.6;
    color: #555;
    margin-bottom: 0.5rem;
  }
  .hint {
    font-size: 0.85rem;
    color: #888;
    margin-top: 1.25rem;
    padding-top: 1.25rem;
    border-top: 1px solid #eee;
  }
</style>
</head>
<body>
<div class="card">
  <div class="icon">
    <svg viewBox="0 0 24 24" fill="none" stroke="#c62828"
         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      <line x1="1" y1="1" x2="23" y2="23"/>
    </svg>
  </div>
  <h1>Access denied</h1>
  <p>Login from external networks is not allowed on this
     Home Assistant instance.</p>
  <p class="hint">Connect from your local network to sign in.</p>
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
