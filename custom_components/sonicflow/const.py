"""SonicFlow integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, LOGGER
from .subsonicApi import SubsonicApi

PLATFORMS: Final[list[Platform]] = [Platform.MEDIA_PLAYER, Platform.MEDIA_SOURCE]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SonicFlow from a config entry."""
    LOGGER.info(f"Setting up SonicFlow integration for {entry.title}")
    
    # Initialize API
    api = SubsonicApi(hass, entry.data)
    
    try:
        # Test connection
        if not await api.ping():
            raise ConfigEntryNotReady("Failed to connect to SonicFlow server")
    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to SonicFlow: {err}") from err
    
    # Store API instance
    hass.data.setdefault(DOMAIN, {})
    hass.data[entry.entry_id] = api
    
    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        del hass.data[DOMAIN][entry.entry_id]
    
    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    LOGGER.debug("Migrating from version %s", config_entry.version)
    
    if config_entry.version == 1:
        # Nothing to migrate for now
        pass
    
    LOGGER.info("Migration to version %s successful", config_entry.version)
    return True
