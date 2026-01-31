"""Config flow for Disable External Login."""

from __future__ import annotations

import ipaddress
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from .const import CONF_ENABLED, CONF_LOCAL_NETWORKS, DEFAULT_LOCAL_NETWORKS, DOMAIN


def _validate_cidrs(values: list[str]) -> list[str]:
    """Validate that each entry is a valid CIDR."""
    for cidr in values:
        try:
            ipaddress.ip_network(cidr.strip(), strict=False)
        except ValueError as err:
            raise vol.Invalid(f"Invalid CIDR: {cidr}") from err
    return values


class DisableExternalLoginConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Disable External Login."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Single instance only
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                _validate_cidrs(user_input[CONF_LOCAL_NETWORKS])
            except vol.Invalid:
                errors[CONF_LOCAL_NETWORKS] = "invalid_cidr"
            else:
                return self.async_create_entry(
                    title="Disable External Login",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENABLED, default=True): bool,
                    vol.Required(
                        CONF_LOCAL_NETWORKS,
                        default=list(DEFAULT_LOCAL_NETWORKS),
                    ): TextSelector(TextSelectorConfig(multiple=True)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> DisableExternalLoginOptionsFlow:
        """Get the options flow."""
        return DisableExternalLoginOptionsFlow()


class DisableExternalLoginOptionsFlow(OptionsFlow):
    """Options flow for Disable External Login."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                _validate_cidrs(user_input[CONF_LOCAL_NETWORKS])
            except vol.Invalid:
                errors[CONF_LOCAL_NETWORKS] = "invalid_cidr"
            else:
                return self.async_create_entry(data=user_input)

        merged = {**self.config_entry.data, **self.config_entry.options}
        current_enabled = merged.get(CONF_ENABLED, True)
        current_networks = merged.get(
            CONF_LOCAL_NETWORKS, list(DEFAULT_LOCAL_NETWORKS)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENABLED, default=current_enabled): bool,
                    vol.Required(
                        CONF_LOCAL_NETWORKS, default=current_networks
                    ): TextSelector(TextSelectorConfig(multiple=True)),
                }
            ),
            errors=errors,
        )
