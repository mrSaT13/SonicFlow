"""Diagnostics support for SonicFlow."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    api = hass.data[DOMAIN].get(entry.entry_id)
    if not api:
        return {"error": "API not available"}

    server_info = api.get_server_info()

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "data": {k: v for k, v in entry.data.items() if k != "password"},
            "options": dict(entry.options),
        },
        "server_info": server_info,
        "server_reachable": await api.ping(hass=hass),
    }
