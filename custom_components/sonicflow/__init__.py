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
    """Set up SonicFlow from a config entry."""
    _LOGGER.info("Setting up SonicFlow integration for %s", entry.title)
    
    # Initialize API with correct signature
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
        # Test connection
        if not await api.ping(hass=hass):
            raise ConfigEntryNotReady("Failed to connect to SonicFlow server")
    except Exception as err:
        await api.close()
        raise ConfigEntryNotReady(f"Error connecting to SonicFlow: {err}") from err
    
    # ✅ ИСПРАВЛЕНО: сохраняем ВНУТРИ DOMAIN, а не в корне hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = api
    
    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # ✅ ИСПРАВЛЕНО: корректная очистка из DOMAIN
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        api = hass.data[DOMAIN][entry.entry_id]
        await api.close()
        del hass.data[DOMAIN][entry.entry_id]
    
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    
    if config_entry.version == 1:
        pass
    
    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True