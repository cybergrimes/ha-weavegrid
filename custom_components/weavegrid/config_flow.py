"""Config flow for the WeaveGrid integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import WeaveGridAuthError, WeaveGridClient, WeaveGridConnectionError
from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    LOGGER,
    POLL_INTERVAL_OPTIONS,
)


class WeaveGridFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a WeaveGrid config flow."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return WeaveGridOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = WeaveGridClient(async_create_clientsession(self.hass))
            try:
                result = await client.login(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except WeaveGridAuthError:
                errors[CONF_PASSWORD] = "invalid_auth"
            except WeaveGridConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(result.user_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=result.utility_acronym.upper(),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): TextSelector(
                        TextSelectorConfig(autocomplete="email")
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle initiation of re-authentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()
            client = WeaveGridClient(async_create_clientsession(self.hass))
            try:
                await client.login(
                    reauth_entry.data[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except WeaveGridAuthError:
                errors[CONF_PASSWORD] = "invalid_auth"
            except WeaveGridConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={
                        CONF_EMAIL: reauth_entry.data[CONF_EMAIL],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )


class WeaveGridOptionsFlowHandler(OptionsFlow):
    """Handle WeaveGrid integration options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the polling interval."""
        if user_input is not None:
            user_input[CONF_POLL_INTERVAL] = int(
                user_input[CONF_POLL_INTERVAL]
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=str(
                            self.config_entry.options.get(
                                CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                            )
                        ),
                    ): SelectSelector(
                        SelectSelectorConfig(options=list(POLL_INTERVAL_OPTIONS))
                    ),
                }
            ),
        )
