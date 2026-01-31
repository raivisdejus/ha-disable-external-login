"""Disable External Login integration."""

from __future__ import annotations

import ipaddress
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ENABLED, CONF_LOCAL_NETWORKS, DEFAULT_LOCAL_NETWORKS, DOMAIN
from .middleware import create_middleware

_LOGGER = logging.getLogger(__name__)


def _parse_networks(
    cidrs: list[str],
) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse a list of CIDR strings into network objects."""
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for cidr in cidrs:
        try:
            networks.append(ipaddress.ip_network(cidr.strip(), strict=False))
        except ValueError:
            _LOGGER.warning("Ignoring invalid CIDR: %s", cidr)
    return networks


def _build_config(entry: ConfigEntry) -> dict:
    """Build the runtime config dict from a config entry."""
    merged = {**entry.data, **entry.options}
    networks = merged.get(CONF_LOCAL_NETWORKS, list(DEFAULT_LOCAL_NETWORKS))
    return {
        CONF_ENABLED: merged.get(CONF_ENABLED, True),
        CONF_LOCAL_NETWORKS: _parse_networks(networks),
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Disable External Login from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = _build_config(entry)

    # Only append middleware once (survives unload/reload)
    if "middleware_installed" not in hass.data[DOMAIN]:

        def get_config() -> dict | None:
            return hass.data.get(DOMAIN, {}).get("config")

        mw = create_middleware(get_config)
        try:
            hass.http.app.middlewares.append(mw)
        except RuntimeError:
            # Middleware list is frozen (C-extension FrozenList, read-only
            # frozen flag). Replace the list and rebuild the handler chain.
            from frozenlist import FrozenList  # noqa: PLC0415

            app = hass.http.app
            new_middlewares = FrozenList(list(app.middlewares) + [mw])
            new_middlewares.freeze()
            app._middlewares = new_middlewares  # noqa: SLF001
            app._middlewares_handlers = tuple(  # noqa: SLF001
                app._prepare_middleware()
            )
            app._run_middlewares = True  # noqa: SLF001
            _LOGGER.info(
                "External login blocking middleware installed "
                "(injected into running server)"
            )
        else:
            _LOGGER.info("External login blocking middleware installed")
        hass.data[DOMAIN]["middleware_installed"] = True

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Handle options update."""
    hass.data[DOMAIN]["config"] = _build_config(entry)
    _LOGGER.info("External login blocking configuration updated")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Disable the middleware by removing config (middleware stays but becomes no-op)
    hass.data[DOMAIN].pop("config", None)
    _LOGGER.info("External login blocking disabled")
    return True
