"""Media player platform for SonicFlow."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN
from ..subsonicApi import SubsonicApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SonicFlow media player from config entry."""
    _LOGGER.debug("Setting up SonicFlow media player for %s", entry.title)
    
    # Get API instance from hass.data
    api: SubsonicApi = hass.data[DOMAIN][entry.entry_id]
    
    # Create and add your media player entity here
    # Example (замените на ваш реальный класс):
    # async_add_entities([SonicFlowMediaPlayer(api, entry)], update_before_add=True)
    
    # ⚠️ ВРЕМЕННО: чтобы интеграция загружалась без реальной сущности
    # Удалите этот блок, когда создадите класс медиаплеера
    _LOGGER.warning(
        "SonicFlow media player entity not implemented yet. "
        "Create your MediaPlayer class and replace this placeholder."
    )