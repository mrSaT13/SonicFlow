"""Config flow for SonicFlow integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_APP,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USER,
    CONF_ARTISTS,
    CONF_ALBUMS,
    CONF_PLAYLISTS,
    CONF_GENRES,
    CONF_RADIO,
    CONF_FAVORITES,
    CONF_SONGS,
    DEFAULT_APP,
    DEFAULT_OPTIONS,
    DOMAIN,
    LOGGER,
    TITLE,
)
from .subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_USER): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_APP, default=DEFAULT_APP): vol.In(
            {
                "subsonic": "Subsonic",
                "navidrome": "Navidrome",
            }
        ),
        vol.Optional("title", default=""): str,
    }
)

STEP_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ARTISTS, default=True): bool,
        vol.Optional(CONF_ALBUMS, default=True): bool,
        vol.Optional(CONF_PLAYLISTS, default=True): bool,
        vol.Optional(CONF_GENRES, default=True): bool,
        vol.Optional(CONF_RADIO, default=False): bool,
        vol.Optional(CONF_FAVORITES, default=True): bool,
        vol.Optional(CONF_SONGS, default=True): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Validate the user input allows us to connect."""
    api = SubsonicApi(hass, data)
    
    # Validate URL format
    url = data.get(CONF_URL, "")
    if not url.startswith(("http://", "https://")):
        raise InvalidUrl
    
    # Test connection
    if not await api.ping():
        raise CannotConnect
    
    return True


class SonicFlowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SonicFlow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidUrl:
                errors["base"] = "invalid_url"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Store title
                app = user_input[CONF_APP]
                title = user_input.get("title", "").strip()
                if not title:
                    title = TITLE.get(app, "SonicFlow")
                
                # Create entry with data and default options
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_URL: user_input[CONF_URL],
                        CONF_USER: user_input[CONF_USER],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_APP: user_input[CONF_APP],
                    },
                    options=DEFAULT_OPTIONS.copy(),
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidUrl:
                errors["base"] = "invalid_url"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        CONF_URL: user_input[CONF_URL],
                        CONF_USER: user_input[CONF_USER],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_APP: user_input[CONF_APP],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, entry.data
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SonicFlowOptionsFlow:
        """Get the options flow for this handler."""
        return SonicFlowOptionsFlow()


class SonicFlowOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for SonicFlow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                STEP_OPTIONS_SCHEMA, self.config_entry.options
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidUrl(HomeAssistantError):
    """Error to indicate invalid URL."""