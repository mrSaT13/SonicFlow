"""SonicFlow integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_URL, CONF_USER, CONF_PASSWORD, CONF_APP
from .subsonicApi import SubsonicApi

PLATFORMS: Final[list[Platform]] = [Platform.MEDIA_PLAYER]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Setting up SonicFlow for %s (ID: %s)", entry.title, entry.entry_id)
    
    api = SubsonicApi(
        userAgent="HomeAssistant/SonicFlow",
        config={
            CONF_URL: entry.data[CONF_URL],
            CONF_USER: entry.data[CONF_USER],
            CONF_PASSWORD: entry.data[CONF_PASSWORD],
            CONF_APP: entry.data[CONF_APP],
        },
        session=None,
    )
    
    try:
        if not await api.ping(hass=hass):
            raise ConfigEntryNotReady("Failed to connect")
    except Exception as err:
        await api.close()
        raise ConfigEntryNotReady(f"Connection error: {err}") from err
    
    # 🔑 КРИТИЧЕСКИ ВАЖНО: Сохраняем строго в hass.data[DOMAIN][entry_id]
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = api
    _LOGGER.info("✅ API stored at hass.data['%s']['%s']", DOMAIN, entry.entry_id)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        api = hass.data[DOMAIN][entry.entry_id]
        await api.close()
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
