"""Media source provider for SonicFlow."""
from __future__ import annotations

from homeassistant.components.media_source.models import MediaSource
from homeassistant.core import HomeAssistant

from ..const import DOMAIN


async def async_get_media_source(hass: HomeAssistant) -> MediaSource:
    """Set up SonicFlow media source."""
    from ..media_source import SubsonicSource

    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return SubsonicSource(hass, None)
    return SubsonicSource(hass, entries[0])
